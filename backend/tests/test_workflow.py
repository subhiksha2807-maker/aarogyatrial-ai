import os
from pathlib import Path

TEST_DB = Path(__file__).parent / "test_aarogya.db"
os.environ["AAROGYA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
from app.main import app


def login(client, username, password):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_complete_workflow():
    if TEST_DB.exists():
        TEST_DB.unlink()
    with TestClient(app) as client:
        coordinator = login(client, "coordinator", "Coord@123")
        pi = login(client, "pi", "PI@123")
        ethics = login(client, "ethics", "Ethics@123")

        before = client.get("/api/dashboard", headers=coordinator).json()["pending_events"]
        created = client.post("/api/adverse-events", headers=coordinator, json={
            "participant_code": "AYU101-P02", "narrative": "Participant experienced a headache after the morning routine.",
            "onset_date": "2026-09-22", "severity": "Mild"
        })
        assert created.status_code == 201
        event = created.json()
        assert event["suggested_category"] == "Headache or dizziness"
        assert event["status"] == "pending"
        assert client.get("/api/dashboard", headers=coordinator).json()["pending_events"] == before + 1

        forbidden = client.post(f"/api/adverse-events/{event['id']}/review", headers=coordinator,
                                json={"decision": "approve", "note": "Looks correct"})
        assert forbidden.status_code == 403

        reviewed = client.post(f"/api/adverse-events/{event['id']}/review", headers=pi,
                               json={"decision": "correct", "corrected_category": "Other reported symptom", "note": "PI correction for demo."})
        assert reviewed.status_code == 200
        assert reviewed.json()["status"] == "corrected"
        assert client.get("/api/dashboard", headers=ethics).json()["pending_events"] == before
        audit = client.get("/api/audit", headers=ethics).json()
        assert any(item["adverse_event_id"] == event["id"] and item["action"] == "REVIEWED" for item in audit)

        forbidden_create = client.post("/api/adverse-events", headers=pi, json={
            "participant_code": "AYU101-P02", "narrative": "A sufficiently long fictional narrative.",
            "onset_date": "2026-09-22", "severity": "Mild"
        })
        assert forbidden_create.status_code == 403

