from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    source: str = Field(
        description="Origin of the evidence, such as kubernetes, prometheus, loki, or jaeger."
    )
    evidence_type: str = Field(
        description="Type of evidence, such as event, metric, log, or trace."
    )
    timestamp: datetime
    namespace: str | None = None
    resource: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
