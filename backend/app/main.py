from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from .database import db_session, initialize_database
from .repository import row, rows, utcnow
from .security import create_token, decode_token, verify_password
from .seed import seed_database
from .suggestions import DEMO_TERMINOLOGY, suggest_category


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    seed_database()
    yield


app = FastAPI(title="AarogyaTrial AI Demo API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class EventCreate(BaseModel):
    participant_code: str = Field(min_length=3, max_length=40)
    narrative: str = Field(min_length=12, max_length=2000)
    onset_date: date
    severity: Literal["Mild", "Moderate", "Severe"]

    @model_validator(mode="after")
    def validate_date(self):
        if self.onset_date > date.today():
            raise ValueError("Onset date cannot be in the future")
        return self


class ReviewRequest(BaseModel):
    decision: Literal["approve", "correct", "reject"]
    corrected_category: str | None = Field(default=None, max_length=120)
    note: str = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def validate_correction(self):
        if self.decision == "correct" and not self.corrected_category:
            raise ValueError("A corrected category is required")
        return self


def current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    user_id = decode_token(authorization[7:])
    user = row("SELECT id, username, display_name, role FROM users WHERE id = ?", (user_id,)) if user_id else None
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is invalid or expired")
    return user


def require_role(*allowed_roles: str):
    def check(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role cannot perform this action")
        return user
    return check


@app.get("/api/health")
def health():
    return {"status": "ok", "demo": True}


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = row("SELECT * FROM users WHERE username = ?", (payload.username.lower().strip(),))
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    profile = {key: user[key] for key in ("id", "username", "display_name", "role")}
    return {"access_token": create_token(user["id"]), "user": profile}


@app.get("/api/me")
def me(user: dict = Depends(current_user)):
    return user


@app.get("/api/dashboard")
def dashboard(_: dict = Depends(current_user)):
    studies = rows("""SELECT s.*, COALESCE(SUM(si.enrolled_count), 0) enrolled_count
        FROM studies s LEFT JOIN sites si ON si.study_id = s.id GROUP BY s.id ORDER BY s.code""")
    pending = row("SELECT COUNT(*) count FROM adverse_events WHERE status = 'pending'")["count"]
    milestones = rows("""SELECT m.*, s.code study_code FROM milestones m JOIN studies s ON s.id = m.study_id
        WHERE m.status != 'completed' ORDER BY m.due_date LIMIT 5""")
    return {"studies": studies, "pending_events": pending, "upcoming_milestones": milestones}


@app.get("/api/studies")
def list_studies(_: dict = Depends(current_user)):
    return rows("""SELECT s.*, COALESCE(SUM(si.enrolled_count), 0) enrolled_count
        FROM studies s LEFT JOIN sites si ON si.study_id = s.id GROUP BY s.id ORDER BY s.code""")


@app.get("/api/studies/{study_id}")
def study_detail(study_id: int, _: dict = Depends(current_user)):
    study = row("SELECT * FROM studies WHERE id = ?", (study_id,))
    if not study:
        raise HTTPException(404, "Study not found")
    study["sites"] = rows("SELECT * FROM sites WHERE study_id = ? ORDER BY code", (study_id,))
    study["participants"] = rows("""SELECT p.code, p.status, si.code site_code FROM participants p
        JOIN sites si ON si.id = p.site_id WHERE p.study_id = ? ORDER BY p.code""", (study_id,))
    study["milestones"] = rows("SELECT * FROM milestones WHERE study_id = ? ORDER BY due_date", (study_id,))
    study["enrolled_count"] = sum(site["enrolled_count"] for site in study["sites"])
    return study


@app.get("/api/participants")
def participants(_: dict = Depends(current_user)):
    return rows("""SELECT p.code, p.status, s.id study_id, s.code study_code, si.code site_code
        FROM participants p JOIN studies s ON s.id = p.study_id JOIN sites si ON si.id = p.site_id ORDER BY p.code""")


EVENT_SELECT = """SELECT ae.*, p.code participant_code, s.code study_code,
    creator.display_name created_by_name, reviewer.display_name reviewed_by_name
    FROM adverse_events ae JOIN participants p ON p.id = ae.participant_id
    JOIN studies s ON s.id = ae.study_id JOIN users creator ON creator.id = ae.created_by
    LEFT JOIN users reviewer ON reviewer.id = ae.reviewed_by"""


@app.get("/api/adverse-events")
def list_events(_: dict = Depends(current_user), event_status: str | None = None):
    query, params = EVENT_SELECT, ()
    if event_status:
        query += " WHERE ae.status = ?"
        params = (event_status,)
    return rows(query + " ORDER BY ae.created_at DESC", params)


@app.post("/api/adverse-events", status_code=201)
def create_event(payload: EventCreate, user: dict = Depends(require_role("coordinator"))):
    participant = row("SELECT id, study_id FROM participants WHERE code = ?", (payload.participant_code.strip().upper(),))
    if not participant:
        raise HTTPException(404, "Participant code was not found")
    category, reason = suggest_category(payload.narrative)
    created_at = utcnow()
    with db_session() as db:
        cursor = db.execute("""INSERT INTO adverse_events (study_id, participant_id, narrative, onset_date, severity,
            suggested_category, suggestion_reason, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (participant["study_id"], participant["id"], payload.narrative.strip(), str(payload.onset_date), payload.severity,
             category, reason, user["id"], created_at))
        event_id = cursor.lastrowid
        db.execute("INSERT INTO audit_entries (adverse_event_id, actor_id, action, detail, created_at) VALUES (?, ?, 'CREATED', ?, ?)",
                   (event_id, user["id"], f"Event submitted; demo suggestion: {category}", created_at))
    return row(EVENT_SELECT + " WHERE ae.id = ?", (event_id,))


@app.post("/api/adverse-events/{event_id}/review")
def review_event(event_id: int, payload: ReviewRequest, user: dict = Depends(require_role("pi"))):
    event = row("SELECT * FROM adverse_events WHERE id = ?", (event_id,))
    if not event:
        raise HTTPException(404, "Adverse event not found")
    if event["status"] != "pending":
        raise HTTPException(409, "This event has already been reviewed")
    final_category = event["suggested_category"] if payload.decision == "approve" else payload.corrected_category if payload.decision == "correct" else None
    reviewed_at = utcnow()
    with db_session() as db:
        reviewed_status = {"approve": "approved", "correct": "corrected", "reject": "rejected"}[payload.decision]
        db.execute("""UPDATE adverse_events SET status = ?, final_category = ?, reviewed_by = ?, reviewed_at = ?, review_note = ?
            WHERE id = ?""", (reviewed_status, final_category,
                              user["id"], reviewed_at, payload.note.strip(), event_id))
        detail = f"Decision: {payload.decision}; final classification: {final_category or 'None'}; note: {payload.note.strip()}"
        db.execute("INSERT INTO audit_entries (adverse_event_id, actor_id, action, detail, created_at) VALUES (?, ?, 'REVIEWED', ?, ?)",
                   (event_id, user["id"], detail, reviewed_at))
    return row(EVENT_SELECT + " WHERE ae.id = ?", (event_id,))


@app.get("/api/audit")
def audit(_: dict = Depends(current_user)):
    return rows("""SELECT a.*, u.display_name actor_name, u.role actor_role, p.code participant_code, s.code study_code
        FROM audit_entries a JOIN users u ON u.id = a.actor_id
        JOIN adverse_events ae ON ae.id = a.adverse_event_id
        JOIN participants p ON p.id = ae.participant_id JOIN studies s ON s.id = ae.study_id
        ORDER BY a.created_at DESC, a.id DESC""")


@app.get("/api/risks")
def risks(_: dict = Depends(current_user)):
    flags = []
    for site in rows("""SELECT si.*, s.code study_code FROM sites si JOIN studies s ON s.id = si.study_id ORDER BY si.code"""):
        if site["enrolled_count"] < site["planned_to_date"]:
            flags.append({"id": f"site-{site['id']}", "level": "Attention", "study_code": site["study_code"],
                          "subject": f"{site['code']} · {site['name']}",
                          "rule": "Enrollment behind plan: enrolled count is below the planned count to date.",
                          "detail": f"{site['enrolled_count']} enrolled vs {site['planned_to_date']} planned to date."})
    for milestone in rows("""SELECT m.*, s.code study_code FROM milestones m JOIN studies s ON s.id = m.study_id
        WHERE m.status = 'overdue' ORDER BY m.due_date"""):
        flags.append({"id": f"milestone-{milestone['id']}", "level": "Overdue", "study_code": milestone["study_code"],
                      "subject": milestone["title"], "rule": "Milestone overdue: status is overdue and work is not completed.",
                      "detail": f"Due {milestone['due_date']}."})
    return {"method": "Transparent deterministic rules — not a trained prediction model.", "flags": flags}


@app.get("/api/demo-terminology")
def terminology(_: dict = Depends(current_user)):
    return {"label": "Demo terminology set (not official MedDRA coding)", "categories": list(DEMO_TERMINOLOGY)}
