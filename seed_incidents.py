
from datetime import datetime, timedelta, timezone

from models.incident import (
    Incident,
    IncidentDNA,
    Timeline,
    Diagnosis,
    Resolution,
    Outcome,
)
from storage.incident_store_sqlite import SQLiteIncidentStore


def main():
    store = SQLiteIncidentStore("data/sentinelops.db")
    now = datetime.now(timezone.utc)

    incidents = [
        Incident(
            id="INC-2407",
            started_at=now - timedelta(minutes=45),
            ended_at=None,
            severity="critical",
            status="open",
            dna=IncidentDNA(
                trigger="memory pressure",
                failure="OOMKilled",
                restart_pattern="repeated container restarts",
                readiness="readiness probe failing",
                affected_workload="payment-api",
                duration=45,
            ),
            timeline=Timeline(entries=[
                {
                    "timestamp": (now - timedelta(minutes=45)).isoformat(),
                    "event": "Memory usage exceeded the container limit.",
                },
                {
                    "timestamp": (now - timedelta(minutes=40)).isoformat(),
                    "event": "Payment API container was OOMKilled and restarted.",
                },
            ]),
            diagnosis=Diagnosis(
                summary="Payment API repeatedly restarts under memory pressure.",
                root_cause="Container memory limit may be too low for current workload.",
                confidence=0.85,
                explanation="Memory pressure coincides with OOMKilled events.",
            ),
            metadata={
                "title": "Payment API memory pressure",
                "service": "payment-api",
                "description": "Repeated OOMKilled events and failed readiness probes.",
            },
        ),
        Incident(
            id="INC-2406",
            started_at=now - timedelta(hours=2),
            severity="high",
            status="open",
            dna=IncidentDNA(
                trigger="database connection saturation",
                failure="connection pool exhausted",
                restart_pattern="none",
                readiness="health check timing out",
                affected_workload="orders-api",
                duration=30,
            ),
            timeline=Timeline(entries=[
                {
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "event": "Database connection pool reached its configured limit.",
                },
                {
                    "timestamp": (now - timedelta(hours=2) + timedelta(minutes=5)).isoformat(),
                    "event": "Orders API health checks began timing out.",
                },
            ]),
            diagnosis=Diagnosis(
                summary="Orders API cannot acquire database connections.",
                root_cause="Database connection pool saturation.",
                confidence=0.8,
                explanation="Connection exhaustion aligns with API health-check timeouts.",
            ),
            metadata={
                "title": "Orders API database connection saturation",
                "service": "orders-api",
                "description": "Connection pool exhaustion causes health-check timeouts.",
            },
        ),
        Incident(
            id="INC-2405",
            started_at=now - timedelta(hours=4),
            ended_at=now - timedelta(hours=3, minutes=50),
            severity="medium",
            status="resolved",
            dna=IncidentDNA(
                trigger="upstream latency spike",
                failure="request timeouts",
                restart_pattern="none",
                readiness="degraded",
                affected_workload="catalog-api",
                duration=10,
            ),
            timeline=Timeline(entries=[
                {
                    "timestamp": (now - timedelta(hours=4)).isoformat(),
                    "event": "Upstream dependency latency increased sharply.",
                },
                {
                    "timestamp": (now - timedelta(hours=3, minutes=50)).isoformat(),
                    "event": "Latency returned to normal after upstream recovery.",
                },
            ]),
            diagnosis=Diagnosis(
                summary="Catalog API experienced elevated request latency.",
                root_cause="Temporary latency spike in an upstream dependency.",
                confidence=0.75,
                explanation="Request timeouts coincided with elevated upstream latency.",
            ),
            resolution=Resolution(
                action="Monitor upstream dependency",
                description="Upstream service recovered and request latency normalized.",
                timestamp=now - timedelta(hours=3, minutes=50),
            ),
            outcome=Outcome(
                status="resolved",
                resolved=True,
                verified=True,
                description="Request latency returned to normal.",
                timestamp=now - timedelta(hours=3, minutes=50),
            ),
            metadata={
                "title": "Catalog API upstream latency",
                "service": "catalog-api",
                "description": "Temporary upstream latency spike caused request timeouts.",
            },
        ),
    ]

    existing_ids = {incident.id for incident in store.list()}
    added = 0

    for incident in incidents:
        if incident.id in existing_ids:
            print(f"Already exists; skipping {incident.id}")
            continue

        store.save(incident)
        added += 1
        print(f"Added {incident.id}: {incident.metadata.get('title')}")

    print(f"\nDone. Added {added} incident(s).")
    print(f"Total incidents in database: {len(store.list())}")


if __name__ == "__main__":
    main()
