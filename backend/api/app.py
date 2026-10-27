from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.errors import APIError
from backend.api.request_context import create_request_id
from backend.api.remediation_routes import router as remediation_router
from backend.api.schemas import (
    DiagnosisResponse,
    ErrorResponse,
    EvidenceResponse,
    IncidentResponse,
    RecommendationResponse,
    TimelineEventResponse,
)
from storage.incident_store_sqlite import SQLiteIncidentStore
from storage.sqlite_evidence_store import SQLiteEvidenceStore

from embeddings.provider import HuggingFaceEmbeddingProvider
from embeddings.service import EmbeddingService
from embeddings.incident_embedding import IncidentEmbeddingService
from embeddings.incident_index import IncidentVectorIndex
from embeddings.vector_store import InMemoryVectorStore
from rag.retriever import IncidentRetriever
from rag.pipeline import RAGPipeline

from diagnosis.engine import DiagnosisEngine
from incident_engine.classifier import IncidentClassifier
from incident_engine.detector import IncidentCandidate
from models.evidence import Evidence

logger = logging.getLogger("sentinelops.api")


app = FastAPI(
    title="SentinelOps API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(remediation_router)

_incident_store: SQLiteIncidentStore | None = None
_evidence_store: SQLiteEvidenceStore | None = None

_rag_pipeline: RAGPipeline | None = None
_incident_index: IncidentVectorIndex | None = None


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline, _incident_index

    if _rag_pipeline is None:
        incident_store = get_incident_store()
        provider = HuggingFaceEmbeddingProvider()
        embedding_service = EmbeddingService(provider)
        incident_embedding_service = IncidentEmbeddingService(
            embedding_service
        )

        vector_store = InMemoryVectorStore(
            dimensions=provider.dimensions
        )

        _incident_index = IncidentVectorIndex(
            incident_embedding_service,
            vector_store,
        )

        historical_incidents = incident_store.list()
        _incident_index.add_incidents(historical_incidents)

        retriever = IncidentRetriever(_incident_index)
        _rag_pipeline = RAGPipeline(retriever)

        logger.info(
            "RAG index initialized",
            extra={
                "indexed_incidents": _incident_index.count(),
                "embedding_dimensions": provider.dimensions,
            },
        )

    return _rag_pipeline

def get_incident_store() -> SQLiteIncidentStore:
    global _incident_store
    if _incident_store is None:
        db_path = os.environ.get("SENTINELOPS_DB_PATH", "data/sentinelops.db")
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        _incident_store = SQLiteIncidentStore(db_path)
    return _incident_store


def get_evidence_store() -> SQLiteEvidenceStore:
    global _evidence_store
    if _evidence_store is None:
        db_path = os.environ.get("SENTINELOPS_DB_PATH", "data/sentinelops.db")
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        _evidence_store = SQLiteEvidenceStore(db_path)
    return _evidence_store


def set_incident_store(store: SQLiteIncidentStore | None) -> None:
    global _incident_store
    _incident_store = store


def set_evidence_store(store: SQLiteEvidenceStore | None) -> None:
    global _evidence_store
    _evidence_store = store


@app.middleware("http")
async def request_id_middleware(
    request: Request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or create_request_id()
    )

    request.state.request_id = request_id

    logger.info(
        "API request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        },
    )

    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "API request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
        )

        return response

    except Exception:
        logger.exception(
            "API request failed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )
        raise


@app.exception_handler(APIError)
async def api_error_handler(
    request: Request,
    exc: APIError,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        create_request_id(),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error,
            message=exc.message,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    request_id = getattr(
        request.state,
        "request_id",
        create_request_id(),
    )

    logger.exception(
        "Unhandled API error",
        extra={
            "request_id": request_id,
        },
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_error",
            message="An internal error occurred.",
            request_id=request_id,
        ).model_dump(),
    )


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "SentinelOps",
        "status": "running",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "version": "1.0.0",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/incidents",
    response_model=list[IncidentResponse],
)
def list_incidents() -> list[IncidentResponse]:
    store = get_incident_store()
    incidents = store.list()
    return [
        IncidentResponse(
            incident_id=getattr(inc, "id", None) or getattr(inc, "incident_id", "unknown"),
            status=getattr(inc, "status", None) or "active",
            severity=getattr(inc, "severity", None) or "warning",
        )
        for inc in incidents
    ]


@app.get(
    "/incidents/{incident_id}",
    response_model=IncidentResponse,
)
def get_incident(
    incident_id: str,
) -> IncidentResponse:
    store = get_incident_store()
    incident = store.get(incident_id)
    if incident is None:
        raise APIError(
            status_code=404,
            error="not_found",
            message=(
                f"Incident '{incident_id}' was not found."
            ),
        )
    return IncidentResponse(
        incident_id=getattr(incident, "id", None) or getattr(incident, "incident_id", incident_id),
        status=getattr(incident, "status", None) or "active",
        severity=getattr(incident, "severity", None) or "warning",
    )


@app.get(
    "/incidents/{incident_id}/timeline",
    response_model=list[TimelineEventResponse],
)
def get_timeline(
    incident_id: str,
) -> list[TimelineEventResponse]:
    store = get_incident_store()
    incident = store.get(incident_id)
    if incident is None or not getattr(incident, "timeline", None):
        return []

    timeline = incident.timeline
    entries = getattr(timeline, "entries", [])
    events: list[TimelineEventResponse] = []
    for entry in entries:
        if isinstance(entry, dict):
            ts = entry.get("timestamp") or datetime.now(timezone.utc)
            src = entry.get("source") or "unknown"
            evt = entry.get("event_type") or entry.get("description") or "event"
            res = entry.get("resource")
            dt = entry.get("data") or {}
        else:
            ts = getattr(entry, "timestamp", None) or datetime.now(timezone.utc)
            src = getattr(entry, "source", None) or "unknown"
            evt = getattr(entry, "event_type", None) or getattr(entry, "description", None) or "event"
            res = getattr(entry, "resource", None)
            dt = getattr(entry, "data", {})
        events.append(
            TimelineEventResponse(
                timestamp=ts,
                source=src,
                event_type=evt,
                resource=res,
                data=dt if isinstance(dt, dict) else {},
            )
        )
    return events



@app.get(
    "/incidents/{incident_id}/diagnosis",
    response_model=DiagnosisResponse,
)
def get_diagnosis(
    incident_id: str,
) -> DiagnosisResponse:
    store = get_incident_store()
    incident = store.get(incident_id)

    if incident is None:
        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=None,
            confidence=None,
        )

    # Preserve existing saved diagnoses for backward compatibility.
    if getattr(incident, "diagnosis", None):
        diag = incident.diagnosis
        summary = (
            getattr(diag, "summary", None)
            or getattr(diag, "root_cause", None)
        )
        confidence = getattr(diag, "confidence", None)

        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=summary,
            confidence=confidence,
        )

    # The stored incident has no dedicated evidence field.
    # Use a timeline entry only when it contains usable current evidence.
    entries = getattr(
        getattr(incident, "timeline", None),
        "entries",
        [],
    ) or []

    if not entries:
        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=None,
            confidence=None,
        )

    entry = entries[-1]
    if not isinstance(entry, dict):
        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=None,
            confidence=None,
        )

    raw_timestamp = entry.get("timestamp") or incident.started_at
    if raw_timestamp is None:
        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=None,
            confidence=None,
        )

    if isinstance(raw_timestamp, str):
        from datetime import datetime
        try:
            raw_timestamp = datetime.fromisoformat(
                raw_timestamp.replace("Z", "+00:00")
            )
        except ValueError:
            return DiagnosisResponse(
                incident_id=incident_id,
                diagnosis=None,
                confidence=None,
            )

    event_text = str(entry.get("event", "")).strip()
    if not event_text:
        return DiagnosisResponse(
            incident_id=incident_id,
            diagnosis=None,
            confidence=None,
        )

    evidence = Evidence(
        source="stored_timeline",
        evidence_type="event",
        timestamp=raw_timestamp,
        namespace=None,
        resource=incident.metadata.get("service"),
        data={"message": event_text},
    )

    candidate = IncidentCandidate(
        detector="StoredTimeline",
        title=incident.metadata.get("title") or event_text,
        severity=incident.severity or "unknown",
        timestamp=raw_timestamp,
        namespace=None,
        resource=incident.metadata.get("service"),
        evidence=evidence,
        details={"event": event_text},
    )

    classification = IncidentClassifier().classify(candidate)

    # Retrieve historical context and pass it into the diagnosis engine.
    rag_result = get_rag_pipeline().run(incident, top_k=5)

    diagnosis = DiagnosisEngine().diagnose(
        candidate,
        classification,
        rag_result=rag_result,
    )

    return DiagnosisResponse(
        incident_id=incident_id,
        diagnosis=diagnosis.summary,
        confidence=diagnosis.confidence,
    )



@app.get(
    "/incidents/{incident_id}/evidence",
    response_model=list[EvidenceResponse],
)
def get_evidence(
    incident_id: str,
) -> list[EvidenceResponse]:
    store = get_evidence_store()
    items = store.search(resource=incident_id)
    responses: list[EvidenceResponse] = []
    for item in items:
        responses.append(
            EvidenceResponse(
                evidence_id=getattr(item, "id", "") or f"{item.source}:{item.evidence_type}",
                source=item.source,
                evidence_type=item.evidence_type,
                timestamp=item.timestamp,
                resource=item.resource,
                data=item.data or {},
            )
        )
    return responses

@app.get("/incidents/{incident_id}/similar")
def get_similar_incidents(
    incident_id: str,
    top_k: int = 5,
) -> dict[str, Any]:
    if top_k < 1 or top_k > 20:
        raise APIError(
            status_code=400,
            error="invalid_top_k",
            message="top_k must be between 1 and 20.",
        )

    incident = get_incident_store().get(incident_id)

    if incident is None:
        raise APIError(
            status_code=404,
            error="not_found",
            message=f"Incident '{incident_id}' was not found.",
        )

    pipeline = get_rag_pipeline()
    result = pipeline.run(incident, top_k=top_k)

    return result.to_dict()
@app.get(
    "/incidents/{incident_id}/recommendations",
    response_model=list[RecommendationResponse],
)
def get_recommendations(
    incident_id: str,
) -> list[RecommendationResponse]:
    store = get_incident_store()
    incident = store.get(incident_id)
    if incident is None or not getattr(incident, "resolution", None):
        return []
    res = incident.resolution
    if not getattr(res, "action", None):
        return []
    return [
        RecommendationResponse(
            recommendation_id=f"rec-{incident_id}-1",
            action=res.action,
            target=getattr(incident, "resource", None),
            parameters=getattr(res, "details", {}) or {},
        )
    ]


_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend"
)
if os.path.isdir(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")