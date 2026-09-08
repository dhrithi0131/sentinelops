from models.evidence import Evidence


def sort_evidence(evidence: list[Evidence]) -> list[Evidence]:
    return sorted(evidence, key=lambda item: item.timestamp)
