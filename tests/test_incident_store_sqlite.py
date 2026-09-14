from datetime import datetime, timezone

from models.incident import Incident
from storage.incident_store_sqlite import SQLiteIncidentStore


def make_incident() -> Incident:
    return Incident(
        id="incident-1",
        timestamp=datetime.now(timezone.utc),
        severity="high",
        status="open",
    )


def test_save_and_get(tmp_path):
    db = tmp_path / "incidents.db"
    store = SQLiteIncidentStore(str(db))

    incident = make_incident()

    incident_id = store.save(incident)

    assert incident_id == "incident-1"
    result = store.get("incident-1")

    assert result is not None
    assert result.id == "incident-1"


def test_persists_across_store_instances(tmp_path):
    db = tmp_path / "incidents.db"

    incident = make_incident()

    first_store = SQLiteIncidentStore(str(db))
    first_store.save(incident)

    second_store = SQLiteIncidentStore(str(db))
    result = second_store.get("incident-1")

    assert result is not None
    assert result.id == "incident-1"


def test_get_missing_returns_none(tmp_path):
    db = tmp_path / "incidents.db"
    store = SQLiteIncidentStore(str(db))

    assert store.get("does-not-exist") is None


def test_delete(tmp_path):
    db = tmp_path / "incidents.db"
    store = SQLiteIncidentStore(str(db))

    store.save(make_incident())

    assert store.delete("incident-1") is True
    assert store.get("incident-1") is None
    assert store.delete("incident-1") is False