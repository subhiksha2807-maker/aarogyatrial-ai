from __future__ import annotations

from datetime import datetime, timezone

from .database import db_session
from .security import hash_password
from .suggestions import suggest_category


def seed_database() -> None:
    with db_session() as db:
        if db.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            return

        users = [
            ("coordinator", "Kavya Rao", "coordinator", "Coord@123"),
            ("pi", "Dr. Arjun Mehta", "pi", "PI@123"),
            ("ethics", "Dr. Meera Sen", "ethics_reviewer", "Ethics@123"),
        ]
        for username, name, role, password in users:
            db.execute(
                "INSERT INTO users (username, display_name, role, password_hash) VALUES (?, ?, ?, ?)",
                (username, name, role, hash_password(password)),
            )

        studies = [
            ("AYU-101", "Ashwagandha Wellness Study", "Fictional study of a standardized botanical wellness routine.", 60, "Active"),
            ("AYU-202", "Triphala Digestive Health Study", "Fictional observational digestive-wellness study.", 40, "Active"),
        ]
        db.executemany("INSERT INTO studies (code, title, description, target_enrollment, status) VALUES (?, ?, ?, ?, ?)", studies)
        study_ids = {row["code"]: row["id"] for row in db.execute("SELECT id, code FROM studies")}

        sites = [
            (study_ids["AYU-101"], "PUN-01", "Pune Ayurveda Research Centre", "Pune", 35, 18, 22),
            (study_ids["AYU-101"], "JAI-02", "Jaipur Integrative Clinic", "Jaipur", 25, 16, 15),
            (study_ids["AYU-202"], "BLR-03", "Bengaluru Wellness Institute", "Bengaluru", 40, 27, 25),
        ]
        db.executemany("INSERT INTO sites (study_id, code, name, city, target_enrollment, enrolled_count, planned_to_date) VALUES (?, ?, ?, ?, ?, ?, ?)", sites)
        site_ids = {row["code"]: row["id"] for row in db.execute("SELECT id, code FROM sites")}

        participants = [
            (study_ids["AYU-101"], site_ids["PUN-01"], "AYU101-P01", "Enrolled"),
            (study_ids["AYU-101"], site_ids["PUN-01"], "AYU101-P02", "Enrolled"),
            (study_ids["AYU-101"], site_ids["JAI-02"], "AYU101-J01", "Enrolled"),
            (study_ids["AYU-202"], site_ids["BLR-03"], "AYU202-B01", "Enrolled"),
            (study_ids["AYU-202"], site_ids["BLR-03"], "AYU202-B02", "Enrolled"),
        ]
        db.executemany("INSERT INTO participants (study_id, site_id, code, status) VALUES (?, ?, ?, ?)", participants)

        milestones = [
            (study_ids["AYU-101"], "Interim safety review", "2026-10-15", "upcoming"),
            (study_ids["AYU-101"], "Site refresher training", "2026-08-30", "overdue"),
            (study_ids["AYU-202"], "Enrollment checkpoint", "2026-11-05", "upcoming"),
            (study_ids["AYU-202"], "Protocol orientation", "2026-07-12", "completed"),
        ]
        db.executemany("INSERT INTO milestones (study_id, title, due_date, status) VALUES (?, ?, ?, ?)", milestones)

        user_ids = {row["username"]: row["id"] for row in db.execute("SELECT id, username FROM users")}
        participant_ids = {row["code"]: row["id"] for row in db.execute("SELECT id, code FROM participants")}
        now = datetime.now(timezone.utc).isoformat()
        seeded_events = [
            ("AYU101-P01", "Participant reported mild nausea after the evening dose.", "2026-09-18", "Mild"),
            ("AYU202-B01", "Participant described an itchy rash on the forearm.", "2026-09-20", "Moderate"),
        ]
        for code, narrative, onset, severity in seeded_events:
            category, reason = suggest_category(narrative)
            participant = db.execute("SELECT study_id FROM participants WHERE code = ?", (code,)).fetchone()
            cursor = db.execute(
                """INSERT INTO adverse_events (study_id, participant_id, narrative, onset_date, severity,
                suggested_category, suggestion_reason, status, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (participant["study_id"], participant_ids[code], narrative, onset, severity, category, reason, user_ids["coordinator"], now),
            )
            db.execute(
                "INSERT INTO audit_entries (adverse_event_id, actor_id, action, detail, created_at) VALUES (?, ?, 'CREATED', ?, ?)",
                (cursor.lastrowid, user_ids["coordinator"], f"Event submitted; demo suggestion: {category}", now),
            )

