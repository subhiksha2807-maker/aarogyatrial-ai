# AarogyaTrial AI Architecture

## 1. Purpose and scope

AarogyaTrial AI is a local hackathon prototype that demonstrates one fictional Ayurveda clinical-trial workflow:

```text
Coordinator reports event
        |
        v
Demo keyword rules suggest a category
        |
        v
PI approves, corrects, or rejects
        |
        v
Dashboard count and audit history reflect the decision
```

The application is not approved for clinical use. It does not implement official medical coding, regulatory compliance, FHIR, ABDM, cryptographic audit protection, or a trained prediction model.

## 2. System context

```text
+-----------------------+          HTTP/JSON          +------------------------+
| React web application |  ------------------------>  | FastAPI application    |
| localhost:5173        |  <------------------------  | localhost:8000         |
|                       |                              |                        |
| - Role-aware UI       |                              | - Authentication       |
| - Forms and views     |                              | - Authorization        |
| - Browser session     |                              | - Validation           |
+-----------------------+                              | - Business rules       |
                                                       +-----------+------------+
                                                                   |
                                                                   | SQL
                                                                   v
                                                       +------------------------+
                                                       | SQLite                 |
                                                       | backend/aarogya.db     |
                                                       +------------------------+
```

The browser never connects directly to the database. All reads and writes go through the backend API, where role permissions and validation are enforced.

## 3. Repository layout

```text
ayush/
|-- frontend/
|   |-- src/
|   |   |-- pages/            Route-level screens
|   |   |-- api.ts            HTTP client and response error handling
|   |   |-- auth.tsx          Browser authentication state
|   |   |-- components.tsx    Shared layout and UI components
|   |   |-- types.ts          Shared frontend TypeScript types
|   |   `-- App.tsx           Routes and role-gated screens
|   |-- tailwind.config.js
|   `-- vite.config.ts
|-- backend/
|   |-- app/
|   |   |-- main.py           FastAPI routes, validation, and role checks
|   |   |-- database.py       Database connection and transaction boundary
|   |   |-- repository.py     Shared query helpers
|   |   |-- schema.sql        Relational schema
|   |   |-- seed.py           Idempotent fictional seed data
|   |   |-- security.py       Password hashing and signed demo tokens
|   |   `-- suggestions.py    Transparent keyword suggestion rules
|   `-- tests/
|       `-- test_workflow.py  Complete workflow and authorization test
|-- API.md
|-- ARCHITECTURE.md
`-- README.md
```

## 4. Frontend architecture

The frontend is a React single-page application built by Vite.

### Routing

| Route | Purpose | Access |
|---|---|---|
| `/login` | Demo sign-in | Public |
| `/` | Operational dashboard | All authenticated roles |
| `/studies` | Study list | All authenticated roles |
| `/studies/:id` | Sites, participants, and milestones | All authenticated roles |
| `/report-event` | Create adverse event | Coordinator only in UI and API |
| `/review` | Review pending suggestions | PI only in UI and API |
| `/risks` | Transparent operational flags | All authenticated roles |
| `/audit` | Event creation and review history | All authenticated roles |

`RoleGate` prevents irrelevant screens from being shown. This is only a usability feature; the backend is the authorization boundary.

### Client state

- The signed access token is stored in browser `localStorage` under `aarogya_token`.
- `AuthProvider` loads the current user from `GET /api/me` after refresh.
- Page data is requested from the backend when a route loads.
- Submitted forms are persisted through the API rather than stored only in React state.

For a production system, replace local storage and the demo token with an appropriately reviewed identity and session solution.

## 5. Backend architecture

The backend is a FastAPI application with four main responsibilities:

1. Parse and validate HTTP input with Pydantic models.
2. Authenticate signed bearer tokens and enforce role permissions.
3. Apply deterministic suggestion and operational-risk rules.
4. Read and modify persistent records inside SQLite transactions.

### Authorization matrix

| Capability | Coordinator | PI | Ethics Reviewer |
|---|:---:|:---:|:---:|
| View dashboard and studies | Yes | Yes | Yes |
| View risk flags and audit history | Yes | Yes | Yes |
| Create adverse event | Yes | No | No |
| Review adverse event | No | Yes | No |

The API returns HTTP `403` when an authenticated role attempts a forbidden action.

## 6. Data model

```text
studies 1 ------ * sites
   |                |
   |                |
   +------ * participants
   |
   +------ * milestones
   |
   +------ * adverse_events * ------ 1 users (creator)
                      |
                      +------------- 0..1 users (reviewer)
                      |
                      +------ * audit_entries * ------ 1 users (actor)
```

### Main entities

- `users`: seeded identities, roles, and PBKDF2 password hashes.
- `studies`: fictional study code, title, target, and status.
- `sites`: site target, current enrollment, and planned enrollment to date.
- `participants`: fictional participant code linked to a study and site.
- `milestones`: due date and operational status.
- `adverse_events`: narrative, severity, provisional suggestion, PI decision, and final reviewed classification.
- `audit_entries`: actor, action, detail, event reference, and timestamp.

Participant records contain fictional codes only. The prototype has no fields for real participant names or contact details.

## 7. Adverse-event sequence

```text
Coordinator UI       FastAPI          Rule engine       SQLite       PI UI
      |                  |                  |               |           |
      | POST event       |                  |               |           |
      |----------------->| validate role    |               |           |
      |                  |----------------->| match terms   |           |
      |                  |<-----------------| suggestion    |           |
      |                  | save pending event + CREATED audit           |
      |                  |--------------------------------->|           |
      |<-----------------| saved event      |               |           |
      |                  |                  |               |           |
      |                  | GET pending events              |<----------|
      |                  |-------------------------------->|           |
      |                  |<--------------------------------|           |
      |                  |-------------------------------------------->|
      |                  |                  |               |           |
      |                  | POST review (approve/correct/reject) <------|
      |                  | validate PI role |               |           |
      |                  | save decision + REVIEWED audit   |           |
      |                  |--------------------------------->|           |
      |                  |-------------------------------------------->|
```

The suggestion is stored separately from `final_category`. A new event always has `status = pending`, and no final classification is assigned until the PI review endpoint is called.

## 8. Suggestion engine

`backend/app/suggestions.py` defines a small demo terminology set and visible keyword lists.

Current categories:

- Gastrointestinal discomfort
- Headache or dizziness
- Skin irritation
- Fatigue or weakness
- Needs manual review

If exactly one category matches, the API returns that category and the matched keywords. If none or multiple categories match, it returns `Needs manual review`. These are prototype labels and are not official MedDRA codes.

## 9. Risk rules

The risk endpoint uses deterministic database comparisons:

- Enrollment flag: `enrolled_count < planned_to_date`.
- Milestone flag: `status = overdue`.

Each API result includes the rule and current values that caused the flag. The application does not describe these rules as a trained model or prediction.

## 10. Authentication design

1. The client sends a username and password to `POST /api/auth/login`.
2. The backend checks the PBKDF2 password hash.
3. The backend issues an HMAC-signed token containing the user ID and an eight-hour expiry.
4. The client sends the token as `Authorization: Bearer <token>`.
5. Each protected endpoint validates the signature, expiry, current user, and required role.

This is deliberately a local-demo design. The fallback signing secret in source code must not be treated as a production secret.

## 11. Persistence and PostgreSQL path

SQLite connection creation and transaction management are centralized in `backend/app/database.py`. Query helpers live in `backend/app/repository.py`, while schema creation is isolated in `schema.sql`.

A PostgreSQL migration should include:

1. Add a database configuration object and PostgreSQL driver.
2. Replace SQLite connection creation with a provider selected by environment configuration.
3. Move route-level SQL into repository classes or functions with database-neutral parameters.
4. Add a migration tool such as Alembic rather than executing `schema.sql` at startup.
5. Replace SQLite-specific automatic IDs and parameter markers where required.
6. Run the workflow and authorization tests against both database providers.

No PostgreSQL driver is included in this prototype, keeping local setup minimal.

## 12. Security and operational boundaries

Implemented for the demo:

- PBKDF2 password hashes with unique salts
- Signed, expiring access tokens
- Backend role checks
- Pydantic request validation
- Parameterized SQL queries
- Explicit CORS allowlist for local frontend origins

Not implemented:

- Production identity provider or multi-factor authentication
- Account lifecycle, password reset, token revocation, or brute-force controls
- TLS termination or deployment hardening
- Encrypted database fields
- Cryptographically chained or immutable audit history
- Backups, monitoring, disaster recovery, or validated compliance controls

## 13. Verification

The automated backend test performs the complete workflow and verifies unauthorized operations:

```cmd
cd /d C:\Users\HP\Downloads\ayush\backend
.venv\Scripts\python.exe -m pytest -q
```

The frontend production check is:

```cmd
cd /d C:\Users\HP\Downloads\ayush\frontend
npm run build
```

