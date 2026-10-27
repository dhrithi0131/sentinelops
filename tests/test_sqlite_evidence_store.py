from datetime import datetime, timezone
import pytest

from models.evidence import Evidence
from storage.sqlite_evidence_store import SQLiteEvidenceStore


def test_save_and_get_round_trip(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    store = SQLiteEvidenceStore(db_path)

    timestamp = datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)
    evidence = Evidence(
        source="prometheus",
        evidence_type="metric",
        timestamp=timestamp,
        namespace="production",
        resource="api-gateway",
        data={
            "metric_name": "container_cpu_usage",
            "current_value": 85.5,
            "baseline": 25.0,
        },
    )

    evidence_id = store.save(evidence)
    assert evidence_id

    retrieved = store.get(evidence_id)
    assert retrieved is not None
    assert retrieved.source == "prometheus"
    assert retrieved.evidence_type == "metric"
    assert retrieved.namespace == "production"
    assert retrieved.resource == "api-gateway"
    assert retrieved.data["metric_name"] == "container_cpu_usage"
    assert retrieved.data["current_value"] == 85.5
    assert retrieved.data["baseline"] == 25.0


def test_search_by_filters(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    store = SQLiteEvidenceStore(db_path)

    t1 = datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 20, 11, 0, 0, tzinfo=timezone.utc)

    e1 = Evidence(
        source="prometheus",
        evidence_type="metric",
        timestamp=t1,
        namespace="prod",
        resource="app-1",
        data={"val": 1},
    )
    e2 = Evidence(
        source="loki",
        evidence_type="log",
        timestamp=t2,
        namespace="prod",
        resource="app-2",
        data={"val": 2},
    )

    store.save(e1)
    store.save(e2)

    by_source = store.search(source="prometheus")
    assert len(by_source) == 1
    assert by_source[0].resource == "app-1"

    by_namespace = store.search(namespace="prod")
    assert len(by_namespace) == 2

    by_resource = store.search(resource="app-2")
    assert len(by_resource) == 1
    assert by_resource[0].source == "loki"


def test_delete_evidence(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    store = SQLiteEvidenceStore(db_path)

    evidence = Evidence(
        source="jaeger",
        evidence_type="trace",
        timestamp=datetime.now(timezone.utc),
        resource="checkout",
        data={"duration_ms": 120},
    )

    evidence_id = store.save(evidence)
    assert store.get(evidence_id) is not None

    deleted = store.delete(evidence_id)
    assert deleted is True
    assert store.get(evidence_id) is None

    # Deleting non-existent returns False
    assert store.delete("non-existent") is False


def test_missing_optional_fields_handled(tmp_path):
    db_path = str(tmp_path / "evidence.db")
    store = SQLiteEvidenceStore(db_path)

    evidence = Evidence(
        source="kubernetes",
        evidence_type="event",
        timestamp=datetime.now(timezone.utc),
        data={"event": "Started"},
    )

    evidence_id = store.save(evidence)
    retrieved = store.get(evidence_id)
    assert retrieved is not None
    assert retrieved.namespace is None
    assert retrieved.resource is None
    assert retrieved.data == {"event": "Started"}
