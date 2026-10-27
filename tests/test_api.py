import importlib

from fastapi.testclient import TestClient

from backend.api.app import app


client = TestClient(app, raise_server_exceptions=False)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_missing_incident_returns_structured_error() -> None:
    response = client.get("/incidents/missing")

    assert response.status_code == 404

    body = response.json()

    assert body["error"] == "not_found"
    assert body["message"] == "Incident 'missing' was not found."
    assert body["request_id"]


def test_timeline_endpoint() -> None:
    response = client.get("/incidents/inc-1/timeline")

    assert response.status_code == 200
    assert response.json() == []


def test_diagnosis_endpoint() -> None:
    response = client.get("/incidents/inc-1/diagnosis")

    assert response.status_code == 200

    body = response.json()

    assert body["incident_id"] == "inc-1"
    assert body["diagnosis"] is None


def test_evidence_endpoint() -> None:
    response = client.get("/incidents/inc-1/evidence")

    assert response.status_code == 200
    assert response.json() == []


def test_recommendations_endpoint() -> None:
    response = client.get("/incidents/inc-1/recommendations")

    assert response.status_code == 200
    assert response.json() == []


def test_request_id_is_preserved() -> None:
    request_id = "test-request-123"

    response = client.get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id


def test_internal_errors_do_not_expose_traceback() -> None:
    from backend.api.app import app

    @app.get("/test-internal-error")
    def internal_error_route():
        raise RuntimeError("secret internal failure")

    response = client.get("/test-internal-error")

    assert response.status_code == 500

    body = response.json()

    assert body["error"] == "internal_error"
    assert body["message"] == "An internal error occurred."
    assert "traceback" not in body
    assert "secret internal failure" not in body
    assert body["request_id"]


def test_diagnosis_without_saved_record_returns_empty_result() -> None:
    response = client.get("/incidents/inc-1/diagnosis")

    assert response.status_code == 200
    assert response.json() == {
        "incident_id": "inc-1",
        "diagnosis": None,
        "confidence": None,
    }

def test_diagnosis_uses_rag_for_incident_without_saved_diagnosis(
    monkeypatch,
) -> None:
    from datetime import datetime, timezone
    from types import SimpleNamespace

    import importlib

    api = importlib.import_module("backend.api.app")
    from models.incident import Incident, IncidentDNA, Timeline

    timestamp = datetime.now(timezone.utc)
    incident = Incident(
        id="INC-RAG-TEST",
        started_at=timestamp,
        ended_at=None,
        severity="high",
        status="open",
        dna=IncidentDNA(
            trigger="memory pressure",
            failure="OOMKilled",
            restart_pattern="repeated restarts",
            readiness="readiness probe failing",
            affected_workload="test-api",
            duration=5,
        ),
        timeline=Timeline(
            entries=[
                {
                    "timestamp": timestamp.isoformat(),
                    "event": "Memory pressure caused an OOMKilled event.",
                }
            ]
        ),
        metadata={"title": "Memory OOMKilled", "service": "test-api"},
    )

    class FakeStore:
        def get(self, incident_id):
            return incident if incident_id == "INC-RAG-TEST" else None

    historical = SimpleNamespace(incident_id="INC-HISTORICAL")
    fake_rag_result = SimpleNamespace(retrieved_incidents=[historical])
    calls = {}

    class FakePipeline:
        def run(self, query_incident, top_k=5):
            calls["query_incident"] = query_incident
            calls["top_k"] = top_k
            return fake_rag_result

    class FakeDiagnosisEngine:
        def diagnose(self, candidate, classification, rag_result=None):
            calls["candidate"] = candidate
            calls["classification"] = classification
            calls["rag_result"] = rag_result
            return SimpleNamespace(
                summary="Resource incident detected: Memory OOMKilled.",
                confidence=0.95,
            )

    monkeypatch.setattr(api, "get_incident_store", lambda: FakeStore())
    monkeypatch.setattr(api, "get_rag_pipeline", lambda: FakePipeline())
    monkeypatch.setattr(api, "DiagnosisEngine", FakeDiagnosisEngine)

    response = client.get("/incidents/INC-RAG-TEST/diagnosis")

    assert response.status_code == 200
    assert calls["rag_result"] is fake_rag_result
    assert calls["query_incident"] is incident
    assert calls["top_k"] == 5
    assert calls["candidate"].evidence.source == "stored_timeline"
    assert response.json()["incident_id"] == "INC-RAG-TEST"
