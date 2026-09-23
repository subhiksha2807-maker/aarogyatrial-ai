from __future__ import annotations

from datetime import datetime, timezone

from .database import db_session


def rows(query: str, params: tuple = ()) -> list[dict]:
    with db_session() as db:
        return [dict(row) for row in db.execute(query, params).fetchall()]


def row(query: str, params: tuple = ()) -> dict | None:
    with db_session() as db:
        result = db.execute(query, params).fetchone()
        return dict(result) if result else None


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

