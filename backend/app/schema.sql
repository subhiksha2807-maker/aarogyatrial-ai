CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('coordinator', 'pi', 'ethics_reviewer')),
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS studies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    target_enrollment INTEGER NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id INTEGER NOT NULL REFERENCES studies(id),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    target_enrollment INTEGER NOT NULL,
    enrolled_count INTEGER NOT NULL,
    planned_to_date INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id INTEGER NOT NULL REFERENCES studies(id),
    site_id INTEGER NOT NULL REFERENCES sites(id),
    code TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id INTEGER NOT NULL REFERENCES studies(id),
    title TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('upcoming', 'completed', 'overdue'))
);

CREATE TABLE IF NOT EXISTS adverse_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    study_id INTEGER NOT NULL REFERENCES studies(id),
    participant_id INTEGER NOT NULL REFERENCES participants(id),
    narrative TEXT NOT NULL,
    onset_date TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Mild', 'Moderate', 'Severe')),
    suggested_category TEXT NOT NULL,
    suggestion_reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'corrected', 'rejected')),
    final_category TEXT,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TEXT,
    review_note TEXT
);

CREATE TABLE IF NOT EXISTS audit_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adverse_event_id INTEGER NOT NULL REFERENCES adverse_events(id),
    actor_id INTEGER NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    created_at TEXT NOT NULL
);

