from collectors.kubernetes_collector import KubernetesCollector


def test_kubernetes_collector_collects_deployments():
    collector = KubernetesCollector()

    evidence = collector.collect_deployments()

    assert isinstance(evidence, list)

    for item in evidence:
        assert item.source == "kubernetes"
        assert item.evidence_type == "deployment"
        assert item.resource is not None
        assert "desired_replicas" in item.data
        assert "ready_replicas" in item.data
