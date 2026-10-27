import csv
from pathlib import Path
import pytest

from embeddings.incident_document import IncidentDocumentBuilder
from rag.rcaeval_adapter import RCAEvalAdapter


def test_adapter_rejects_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        RCAEvalAdapter(
            tmp_path / "does-not-exist.csv"
        ).load_incidents()


def test_adapter_rejects_missing_required_columns(tmp_path: Path):
    feature_file = tmp_path / "invalid.csv"
    with open(feature_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "service"])
        writer.writeheader()
        writer.writerow({"case_id": "case-1", "service": "adservice"})

    with pytest.raises(ValueError, match="missing columns"):
        RCAEvalAdapter(feature_file).load_incidents()


def test_adapter_loads_valid_fixture(tmp_path: Path):
    feature_file = tmp_path / "rcaeval_fixture.csv"
    with open(feature_file, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "case_id",
            "service",
            "fault_type",
            "injection_time",
            "cpu_mean_delta",
            "memory_mean_delta",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "test-case-01",
                "service": "api-gateway",
                "fault_type": "pod_failure",
                "injection_time": "1700000000",
                "cpu_mean_delta": "42.5",
                "memory_mean_delta": "18.2",
            }
        )

    adapter = RCAEvalAdapter(feature_file)
    incidents = adapter.load_incidents()

    assert len(incidents) == 1
    incident = incidents[0]
    assert incident.incident_id == "rcaeval:test-case-01"
    assert incident.metadata["source"] == "RCAEval"
    assert incident.metadata["outcome_verified"] is False
    assert incident.metadata["service"] == "api-gateway"
    assert incident.metadata["telemetry_features"]["cpu_mean_delta"] == 42.5

    document = IncidentDocumentBuilder().build(incident)
    assert "Incident ID: rcaeval:test-case-01" in document
    assert "api-gateway" in document
    assert "fault_type" not in document.lower()


def test_index_service_indexes_rcaeval_cases(tmp_path: Path):
    from embeddings.incident_index import IncidentVectorIndex
    from embeddings.incident_embedding import IncidentEmbeddingService
    from embeddings.service import EmbeddingService
    from embeddings.vector_store import InMemoryVectorStore
    from rag.embeddings.provider import DeterministicEmbeddingProvider
    from rag.rcaeval_index_service import RCAEvalIndexService

    feature_file = tmp_path / "rcaeval_fixture.csv"
    with open(feature_file, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "case_id",
            "service",
            "fault_type",
            "injection_time",
            "cpu_mean_delta",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "case_id": "test-case-02",
                "service": "payments",
                "fault_type": "network_delay",
                "injection_time": "1700000000",
                "cpu_mean_delta": "12.0",
            }
        )

    provider = DeterministicEmbeddingProvider(dimensions=32)
    embedding_service = EmbeddingService(provider)
    incident_embedding_service = IncidentEmbeddingService(embedding_service)
    vector_store = InMemoryVectorStore(dimensions=32)
    index = IncidentVectorIndex(incident_embedding_service, vector_store)

    service = RCAEvalIndexService(index, feature_file)
    indexed_count = service.index_cases()

    assert indexed_count == 1
    assert index.count() == 1

