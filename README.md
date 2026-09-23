# AarogyaTrial AI

A local hackathon prototype for demonstrating one accountable Ayurveda clinical-trial workflow: a Coordinator reports a fictional adverse event, a transparent keyword engine proposes a **demo terminology** category, a Principal Investigator (PI) explicitly reviews it, and the dashboard and audit history update from persisted SQLite data.

> **Demonstration only:** All studies, sites, participants, events, and people are fictional. This is not approved for clinical use. It does not claim regulatory compliance, official medical coding, FHIR/ABDM support, or cryptographic audit protection.

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS
- Backend: FastAPI and SQLite
- Data access: SQL isolated behind `backend/app/repository.py` and the API layer so a PostgreSQL repository can be added later
- Suggestion engine: local, deterministic keyword rules; no API key or external AI service

Detailed technical documentation:

- [Architecture](ARCHITECTURE.md)
- [API and authentication reference](API.md)

## Run locally on Windows 11 (Command Prompt)

Prerequisites: Python 3.11+ and Node.js 20+.

Open **Command Prompt window 1** for the backend:

```cmd
cd /d C:\Users\HP\Downloads\ayush\backend
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open **Command Prompt window 2** for the frontend:

```cmd
cd /d C:\Users\HP\Downloads\ayush\frontend
npm install
npm run dev
```

Open:

- Web app: http://localhost:5173
- API documentation: http://localhost:8000/docs
- API health check: http://localhost:8000/api/health

SQLite is created automatically as `backend\aarogya.db` on first startup. Saved reports and reviews remain after refreshes and restarts. To return to the original seed data, stop the backend, delete only `backend\aarogya.db`, and restart it.

## Demo credentials

| Role | Username | Password |
|---|---|---|
| Coordinator | `coordinator` | `Coord@123` |
| Principal Investigator | `pi` | `PI@123` |
| Ethics Reviewer | `ethics` | `Ethics@123` |

## Suggested demo flow

1. Sign in as **Coordinator**, open **Report event**, and submit an event for a fictional participant code. A narrative containing “headache,” for example, suggests “Headache or dizziness.” Ambiguous or unmatched text becomes “Needs manual review.”
2. Sign out and sign in as **PI**. Open **PI review**, then approve, correct, or reject the suggestion and enter a note.
3. Check **Overview** to see the pending count update and **Audit history** to see both actors, the decision, and timestamps.
4. Open **Risk rules** to see why the Pune site and overdue milestone are flagged.

The API independently enforces role permissions: only Coordinators can create events and only PIs can review them. Hiding navigation is only a convenience, not the security boundary.

## Verification

Frontend production build:

```cmd
cd /d C:\Users\HP\Downloads\ayush\frontend
npm run build
```

Backend workflow test:

```cmd
cd /d C:\Users\HP\Downloads\ayush\backend
.venv\Scripts\python.exe -m pytest -q
```

## Implemented

- Three seeded roles with password hashing, expiring signed demo sessions, and backend authorization checks
- Database-backed dashboard, study/site enrollment, coded participants, and milestones
- Persistent adverse-event reporting with field validation and useful API errors
- Small, explicitly non-official demo terminology with suggestion reasons and manual-review fallback
- PI approve/correct/reject workflow; suggestions are never finalized automatically
- Transparent enrollment and overdue-milestone risk rules with the triggering condition shown
- Visible audit history for creation and review actions
- Responsive clinical-white and teal interface

## Later work

- Production identity provider, account administration, session revocation, and secret management
- Database migrations and a PostgreSQL repository/provider
- Study configuration, participant enrollment, exports, filtering, pagination, and richer automated tests
- Validated clinical terminology and regulatory workflows only after appropriate governance and verification
