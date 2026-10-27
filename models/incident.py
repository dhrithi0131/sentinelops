from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentDNA(BaseModel):
    """Deterministic fingerprint describing an incident."""

    trigger: str | None = None
    failure: str | None = None
    restart_pattern: str | None = None
    readiness: str | None = None
    affected_workload: str | None = None
    duration: float | None = None
    severity: str | None = None
    dependency_information: dict[str, Any] | None = Field(default_factory=dict)
    anomaly_information: dict[str, Any] | None = Field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class Timeline(BaseModel):
    """Chronological evidence associated with an incident."""

    entries: list[Any] = Field(default_factory=list)


class Diagnosis(BaseModel):
    """Evidence-grounded diagnosis of an incident."""

    summary: str | None = None
    root_cause: str | None = None
    confidence: float | None = None
    evidence: list[Any] = Field(default_factory=list)
    evidence_references: list[Any] = Field(default_factory=list)
    timeline_references: list[Any] = Field(default_factory=list)
    similar_incidents: list[Any] = Field(default_factory=list)
    explanation: str | None = None


IncidentDiagnosis = Diagnosis
IncidentTimeline = Timeline


class Resolution(BaseModel):
    """Resolution information for an incident."""

    action: str | None = None
    description: str | None = None
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


IncidentResolution = Resolution


class Outcome(BaseModel):
    """Observed outcome after incident handling."""

    status: str | None = None
    resolved: bool = False
    verified: bool = False
    description: str | None = None
    timestamp: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


IncidentOutcome = Outcome


class Incident(BaseModel):
    """Storage-independent domain model representing an incident."""

    id: str = Field(default="")
    started_at: datetime | None = None
    ended_at: datetime | None = None
    severity: str | None = None
    status: str | None = None

    dna: IncidentDNA | None = None
    timeline: Timeline | None = None
    diagnosis: Diagnosis | None = None
    resolution: Resolution | None = None
    outcome: Outcome | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    def __init__(
        self,
        id: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        severity: str | None = None,
        status: str | None = None,
        dna: IncidentDNA | None = None,
        timeline: Timeline | None = None,
        diagnosis: Diagnosis | None = None,
        resolution: Resolution | None = None,
        outcome: Outcome | None = None,
        metadata: dict[str, Any] | None = None,
        *,
        incident_id: str | None = None,
        timestamp: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        resolved_id = incident_id if incident_id is not None else (id or kwargs.pop("id", ""))
        resolved_started_at = (
            started_at
            if started_at is not None
            else (timestamp or kwargs.pop("timestamp", None))
        )
        resolved_dna = dna.to_dict() if (dna is not None and hasattr(dna, "to_dict")) else dna
        resolved_diagnosis = (
            diagnosis.to_dict()
            if (diagnosis is not None and hasattr(diagnosis, "to_dict"))
            else diagnosis
        )
        super().__init__(
            id=resolved_id,
            started_at=resolved_started_at,
            ended_at=ended_at,
            severity=severity,
            status=status,
            dna=resolved_dna,
            timeline=timeline,
            diagnosis=resolved_diagnosis,
            resolution=resolution,
            outcome=outcome,
            metadata=metadata or {},
            **kwargs,
        )

    @property
    def incident_id(self) -> str:
        return self.id

    @incident_id.setter
    def incident_id(self, value: str) -> None:
        self.id = value

    @property
    def timestamp(self) -> datetime | None:
        return self.started_at