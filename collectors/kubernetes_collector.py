from datetime import datetime, timezone

from kubernetes import client, config

from collectors.base import BaseCollector
from models.evidence import Evidence


class KubernetesCollector(BaseCollector):
    def __init__(self):
        config.load_kube_config()
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def collect(self) -> list[Evidence]:
        evidence = []

        evidence.extend(self.collect_pods())
        evidence.extend(self.collect_events())
        evidence.extend(self.collect_deployments())
        evidence.extend(self.collect_services())

        return evidence

    def collect_pods(self, namespace: str = "default") -> list[Evidence]:
        pods = self.core_api.list_namespaced_pod(namespace)

        evidence = []

        for pod in pods.items:
            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="pod",
                    timestamp=datetime.now(timezone.utc),
                    namespace=namespace,
                    resource=pod.metadata.name,
                    data={
                        "phase": pod.status.phase,
                        "pod_ip": pod.status.pod_ip,
                        "node_name": pod.spec.node_name,
                    },
                )
            )

        return evidence

    def collect_events(self, namespace: str = "default") -> list[Evidence]:
        events = self.core_api.list_namespaced_event(namespace)

        evidence = []

        for event in events.items:
            event_time = (
                event.last_timestamp
                or event.event_time
                or event.first_timestamp
                or datetime.now(timezone.utc)
            )

            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)

            resource_name = None

            if event.involved_object:
                resource_name = event.involved_object.name

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="event",
                    timestamp=event_time,
                    namespace=namespace,
                    resource=resource_name,
                    data={
                        "reason": event.reason,
                        "message": event.message,
                        "type": event.type,
                        "count": event.count,
                        "kind": (
                            event.involved_object.kind
                            if event.involved_object
                            else None
                        ),
                    },
                )
            )

        return evidence

    def collect_deployments(self, namespace: str = "default") -> list[Evidence]:
        deployments = self.apps_api.list_namespaced_deployment(namespace)

        evidence = []

        for deployment in deployments.items:
            status = deployment.status
            spec = deployment.spec

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="deployment",
                    timestamp=datetime.now(timezone.utc),
                    namespace=namespace,
                    resource=deployment.metadata.name,
                    data={
                        "desired_replicas": spec.replicas,
                        "available_replicas": status.available_replicas or 0,
                        "ready_replicas": status.ready_replicas or 0,
                        "updated_replicas": status.updated_replicas or 0,
                    },
                )
            )

        return evidence

    def collect_services(self, namespace: str = "default") -> list[Evidence]:
        services = self.core_api.list_namespaced_service(namespace)

        evidence = []

        for service in services.items:
            ports = []

            for port in service.spec.ports or []:
                ports.append(
                    {
                        "name": port.name,
                        "port": port.port,
                        "target_port": str(port.target_port),
                        "protocol": port.protocol,
                    }
                )

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="service",
                    timestamp=datetime.now(timezone.utc),
                    namespace=namespace,
                    resource=service.metadata.name,
                    data={
                        "type": service.spec.type,
                        "cluster_ip": service.spec.cluster_ip,
                        "selector": service.spec.selector or {},
                        "ports": ports,
                    },
                )
            )

        return evidence
