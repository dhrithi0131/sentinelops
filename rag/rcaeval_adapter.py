import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from incident_engine.dna import IncidentDNA
from models.incident import Incident, IncidentDiagnosis


class RCAEvalAdapter:
    """Convert RCAEval feature rows into searchable historical incidents."""

    def __init__(self, feature_csv: str | Path) -> None:
        self.feature_csv = Path(feature_csv)

    def load_incidents(self) -> list[Incident]:
        if not self.feature_csv.exists():
            raise FileNotFoundError(
                f"RCAEval feature file not found: {self.feature_csv}"
            )

        with open(self.feature_csv, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
            required = {
                "case_id", "service", "fault_type", "injection_time"
            }
            missing = required - fieldnames
            if missing:
                raise ValueError(
                    f"RCAEval feature file is missing columns: {sorted(missing)}"
                )

            incidents = []
            for row in reader:
                telemetry: dict[str, Any] = {}
                for key, val in row.items():
                    if not key or key in required or key in {"pre_rows", "post_rows"}:
                        continue
                    try:
                        f_val = float(val)
                        telemetry[key] = round(f_val, 6)
                    except (ValueError, TypeError):
                        pass

                try:
                    ts_float = float(row["injection_time"])
                    timestamp = datetime.fromtimestamp(ts_float, tz=timezone.utc)
                except (ValueError, TypeError):
                    timestamp = datetime.now(timezone.utc)

                searchable_signals = {
                    key: value for key, value in telemetry.items()
                    if key.endswith("_mean_delta")
                }
                summary = ", ".join(
                    f"{key}={value}" for key, value in
                    list(searchable_signals.items())[:30]
                ) or "No numeric telemetry deltas available"

                try:
                    inj_time_int = int(float(row["injection_time"]))
                except (ValueError, TypeError):
                    inj_time_int = 0

                incident = Incident(
                    incident_id=f"rcaeval:{row['case_id']}",
                    started_at=timestamp,
                    dna=IncidentDNA(
                        trigger=f"Observed telemetry around service {row['service']}",
                        failure="Telemetry change detected around injection time",
                        affected_workload=str(row["service"]),
                    ),
                    diagnosis=IncidentDiagnosis(
                        summary=(
                            f"Historical telemetry case for service "
                            f"{row['service']}. Observed signals: {summary}"
                        )
                    ),
                    metadata={
                        "source": "RCAEval",
                        "service": str(row["service"]),
                        "fault_type": str(row["fault_type"]),
                        "injection_time": inj_time_int,
                        "telemetry_features": telemetry,
                        "outcome_verified": False,
                    },
                )
                incidents.append(incident)

        return incidents
