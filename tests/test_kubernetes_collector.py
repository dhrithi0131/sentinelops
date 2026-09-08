from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_pods():
    collector = KubernetesCollector()

    evidence = collector.collect_pods()

    assert isinstance(evidence, list)
    assert len(evidence) >= 1

    for item in evidence:
        assert item.source == "kubernetes"
        assert item.evidence_type == "pod"
        assert item.resource is not None
