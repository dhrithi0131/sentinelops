from datetime import datetime

from models.evidence import Evidence


def test_create_evidence():
    evidence = Evidence(
        source="kubernetes",
        evidence_type="event",
        timestamp=datetime.now(),
        namespace="default",
        resource="nginx-demo",
        data={"reason": "Started"},
    )

    assert evidence.source == "kubernetes"
    assert evidence.resource == "nginx-demo"
