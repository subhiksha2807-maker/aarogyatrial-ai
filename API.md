# AarogyaTrial AI API Reference

## Overview

Base URL:

```text
http://localhost:8000/api
```

Interactive OpenAPI documentation is available while the backend is running:

```text
http://localhost:8000/docs
```

All records are fictional. This API is a local demonstration and is not approved for clinical use.

## API key and authentication

### No API key is required

This prototype does **not** use an OpenAI key, external AI service, paid API, or application API key. Do not add an API key to the frontend source code.

Protected endpoints use a short-lived demo bearer token obtained through the login endpoint:

```http
Authorization: Bearer <access_token>
```

The token is HMAC-signed by the backend and expires after eight hours. It is intended only for local demonstration.

### Optional signing-secret configuration

The backend supports an optional environment variable named `AAROGYA_DEMO_SECRET`. This is a token-signing secret, not a client API key.

Command Prompt example:

```cmd
set AAROGYA_DEMO_SECRET=replace-with-a-long-random-local-secret
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

If it is not set, the application uses a known development fallback. Never use that fallback for a deployed system.

## Demo users

| Role | Username | Password |
|---|---|---|
| Coordinator | `coordinator` | `Coord@123` |
| Principal Investigator | `pi` | `PI@123` |
| Ethics Reviewer | `ethics` | `Ethics@123` |

## Common response codes

| Code | Meaning |
|---|---|
| `200` | Request succeeded |
| `201` | Adverse event created |
| `401` | Missing, invalid, or expired bearer token |
| `403` | Authenticated role is not allowed to perform the action |
| `404` | Requested record or participant code was not found |
| `409` | Event was already reviewed |
| `422` | Request body failed validation |

Error response example:

```json
{
  "detail": "Your role cannot perform this action"
}
```

Validation errors use FastAPI's structured `detail` array.

## Authentication endpoints

### `POST /auth/login`

Public. Validates a demo user and returns an access token and user profile.

Request:

```json
{
  "username": "coordinator",
  "password": "Coord@123"
}
```

Response:

```json
{
  "access_token": "signed-demo-token",
  "user": {
    "id": 1,
    "username": "coordinator",
    "display_name": "Kavya Rao",
    "role": "coordinator"
  }
}
```

Command Prompt using curl:

```cmd
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"coordinator\",\"password\":\"Coord@123\"}"
```

### `GET /me`

Authentication: any valid bearer token.

Returns the profile represented by the current token.

```json
{
  "id": 1,
  "username": "coordinator",
  "display_name": "Kavya Rao",
  "role": "coordinator"
}
```

## Health endpoint

### `GET /health`

Public. Used to confirm that the API is running.

```json
{
  "status": "ok",
  "demo": true
}
```

## Dashboard endpoints

### `GET /dashboard`

Authentication: any role.

Returns database-backed studies, enrollment totals, pending-event count, and open milestones.

```json
{
  "studies": [
    {
      "id": 1,
      "code": "AYU-101",
      "title": "Ashwagandha Wellness Study",
      "description": "Fictional study description.",
      "target_enrollment": 60,
      "status": "Active",
      "enrolled_count": 34
    }
  ],
  "pending_events": 2,
  "upcoming_milestones": []
}
```

## Study endpoints

### `GET /studies`

Authentication: any role.

Returns all fictional studies and aggregated enrollment counts.

### `GET /studies/{study_id}`

Authentication: any role.

Returns one study with:

- Sites and their target/current/planned enrollment
- Fictional coded participants
- Milestones
- Aggregated enrollment count

Example:

```cmd
curl http://localhost:8000/api/studies/1 -H "Authorization: Bearer YOUR_TOKEN"
```

### `GET /participants`

Authentication: any role.

Returns fictional participant codes for the report form.

```json
[
  {
    "code": "AYU101-P01",
    "status": "Enrolled",
    "study_id": 1,
    "study_code": "AYU-101",
    "site_code": "PUN-01"
  }
]
```

## Adverse-event endpoints

### `GET /adverse-events`

Authentication: any role.

Optional query parameter:

| Parameter | Example | Purpose |
|---|---|---|
| `event_status` | `pending` | Filter by event status |

Valid stored statuses are `pending`, `approved`, `corrected`, and `rejected`.

Example:

```cmd
curl "http://localhost:8000/api/adverse-events?event_status=pending" -H "Authorization: Bearer YOUR_TOKEN"
```

### `POST /adverse-events`

Authentication: **Coordinator only**.

Creates and persists an event, generates a provisional demo suggestion, and writes a `CREATED` audit entry.

Request:

```json
{
  "participant_code": "AYU101-P02",
  "narrative": "Participant reported a headache after the fictional morning routine.",
  "onset_date": "2026-09-23",
  "severity": "Mild"
}
```

Validation:

- `participant_code`: must identify a seeded fictional participant.
- `narrative`: 12–2000 characters.
- `onset_date`: cannot be in the future.
- `severity`: `Mild`, `Moderate`, or `Severe`.

Selected response fields:

```json
{
  "id": 3,
  "participant_code": "AYU101-P02",
  "study_code": "AYU-101",
  "narrative": "Participant reported a headache after the fictional morning routine.",
  "severity": "Mild",
  "suggested_category": "Headache or dizziness",
  "suggestion_reason": "Matched demo keyword(s): headache.",
  "status": "pending",
  "final_category": null,
  "created_by_name": "Kavya Rao"
}
```

The suggestion is not a final classification.

### `POST /adverse-events/{event_id}/review`

Authentication: **PI only**.

Reviews an event that currently has `status = pending`. The endpoint also writes a `REVIEWED` audit entry.

Approve the suggestion:

```json
{
  "decision": "approve",
  "corrected_category": null,
  "note": "Narrative supports the proposed demo category."
}
```

Correct the suggestion:

```json
{
  "decision": "correct",
  "corrected_category": "Other reported symptom",
  "note": "PI selected a more appropriate classification for this demonstration."
}
```

Reject the suggestion:

```json
{
  "decision": "reject",
  "corrected_category": null,
  "note": "Narrative does not support the suggested category."
}
```

Decision behavior:

| Decision | Stored status | Final category |
|---|---|---|
| `approve` | `approved` | Copies the provisional suggestion after PI action |
| `correct` | `corrected` | Uses the PI-provided `corrected_category` |
| `reject` | `rejected` | Remains `null` |

A second review attempt returns HTTP `409`.

## Audit endpoint

### `GET /audit`

Authentication: any role.

Returns newest-first event creation and review entries.

```json
[
  {
    "id": 4,
    "adverse_event_id": 3,
    "actor_name": "Dr. Arjun Mehta",
    "actor_role": "pi",
    "action": "REVIEWED",
    "detail": "Decision: approve; final classification: Headache or dizziness; note: Reviewed.",
    "created_at": "2026-09-23T12:00:00+00:00",
    "participant_code": "AYU101-P02",
    "study_code": "AYU-101"
  }
]
```

This is a readable database history, not a cryptographically immutable audit ledger.

## Risk endpoint

### `GET /risks`

Authentication: any role.

Returns deterministic operational flags with their triggering rules.

```json
{
  "method": "Transparent deterministic rules — not a trained prediction model.",
  "flags": [
    {
      "id": "site-1",
      "level": "Attention",
      "study_code": "AYU-101",
      "subject": "PUN-01 · Pune Ayurveda Research Centre",
      "rule": "Enrollment behind plan: enrolled count is below the planned count to date.",
      "detail": "18 enrolled vs 22 planned to date."
    }
  ]
}
```

## Demo terminology endpoint

### `GET /demo-terminology`

Authentication: any role.

Returns the labels supported by the local suggestion rules.

```json
{
  "label": "Demo terminology set (not official MedDRA coding)",
  "categories": [
    "Gastrointestinal discomfort",
    "Headache or dizziness",
    "Skin irritation",
    "Fatigue or weakness"
  ]
}
```

Unmatched or ambiguous text produces `Needs manual review` even though it is not listed as a terminology category.

## Complete Command Prompt example

The following uses `curl` and requires copying the returned token into the next command:

```cmd
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d "{\"username\":\"coordinator\",\"password\":\"Coord@123\"}"

set AAROGYA_TOKEN=PASTE_ACCESS_TOKEN_HERE

curl http://localhost:8000/api/dashboard -H "Authorization: Bearer %AAROGYA_TOKEN%"
```

## Database location override

The default SQLite file is `backend\aarogya.db`. Tests and local tools may select another file with:

```cmd
set AAROGYA_DB_PATH=C:\path\to\another-demo.db
```

The path must be set before the backend process starts.

