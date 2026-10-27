from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient

from backend.api.app import (
    app,
    set_incident_store,
    set_evidence_store,
)
from backend.main import app as main_app
from models.incident import Incident, Diagnosis, Resolution, Timeline
from models.evidence import Evidence
from storage.incident_store_sqlite import SQLiteIncidentStore
from storage.sqlite_evidence_store import SQLiteEvidenceStore


def test_main_app_is_canonical_app():
    assert main_app is app


def test_root_endpoint():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "SentinelOps"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"


def test_list_incidents_and_retrieve_stored_incident(tmp_path: Path):
    db_file = str(tmp_path / "test_api.db")
    test_incident_store = SQLiteIncidentStore(db_file)
    test_evidence_store = SQLiteEvidenceStore(db_file)
    set_incident_store(test_incident_store)
    set_evidence_store(test_evidence_store)

    try:
        client = TestClient(app, raise_server_exceptions=False)

        # Initially empty list
        response = client.get("/incidents")
        assert response.status_code == 200
        assert response.json() == []

        # Save an incident
        incident = Incident(
            id="INC-TEST-99",
            status="investigating",
            severity="critical",
            diagnosis=Diagnosis(
                summary="CPU throttling caused by thread starvation.",
                confidence=0.92,
            ),
            resolution=Resolution(
                action="scale_deployment",
                details={"replicas": 5},
            ),
            timeline=Timeline(
                entries=[
                    {
                        "source": "prometheus",
                        "event_type": "metric_anomaly",
                        "description": "High CPU utilization",
                        "resource": "api-gateway",
                        "data": {"value": 0.98},
                        "timestamp": datetime.now(timezone.utc),
                    }
                ]
            ),
        )
        test_incident_store.save(incident)

        # Save evidence
        test_evidence_store.save(
            Evidence(
                source="prometheus",
                evidence_type="metric",
                timestamp=datetime.now(timezone.utc),
                resource="INC-TEST-99",
                data={"metric_name": "container_cpu_usage", "value": 98.0},
            )
        )

        # Test GET /incidents
        list_res = client.get("/incidents")
        assert list_res.status_code == 200
        incidents = list_res.json()
        assert len(incidents) == 1
        assert incidents[0]["incident_id"] == "INC-TEST-99"
        assert incidents[0]["severity"] == "critical"

        # Test GET /incidents/INC-TEST-99
        get_res = client.get("/incidents/INC-TEST-99")
        assert get_res.status_code == 200
        assert get_res.json()["incident_id"] == "INC-TEST-99"

        # Test GET /incidents/INC-TEST-99/diagnosis
        diag_res = client.get("/incidents/INC-TEST-99/diagnosis")
        assert diag_res.status_code == 200
        assert "CPU throttling" in diag_res.json()["diagnosis"]
        assert diag_res.json()["confidence"] == 0.92

        # Test GET /incidents/INC-TEST-99/timeline
        time_res = client.get("/incidents/INC-TEST-99/timeline")
        assert time_res.status_code == 200
        events = time_res.json()
        assert len(events) == 1
        assert events[0]["source"] == "prometheus"

        # Test GET /incidents/INC-TEST-99/evidence
        evi_res = client.get("/incidents/INC-TEST-99/evidence")
        assert evi_res.status_code == 200
        evidence_items = evi_res.json()
        assert len(evidence_items) == 1
        assert evidence_items[0]["data"]["metric_name"] == "container_cpu_usage"

        # Test GET /incidents/INC-TEST-99/recommendations
        rec_res = client.get("/incidents/INC-TEST-99/recommendations")
        assert rec_res.status_code == 200
        recs = rec_res.json()
        assert len(recs) == 1
        assert recs[0]["action"] == "scale_deployment"
        assert recs[0]["parameters"]["replicas"] == 5
    finally:
        set_incident_store(None)
        set_evidence_store(None)
