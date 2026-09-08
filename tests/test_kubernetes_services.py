from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_services():
    collector = KubernetesCollector()

    evidence = collector.collect_services()

    assert isinstance(evidence, list)
    assert len(evidence) >= 1

    for item in evidence:
        assert item.source == "kubernetes"
        assert item.evidence_type == "service"
        assert item.resource is not None
        assert "type" in item.data
        assert "ports" in item.data
