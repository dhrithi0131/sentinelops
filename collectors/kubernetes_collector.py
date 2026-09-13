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
        evidence.extend(self.collect_nodes())

        return evidence

    def collect_pods(self) -> list[Evidence]:
        pods = self.core_api.list_pod_for_all_namespaces()

        evidence = []

        for pod in pods.items:
            containers = []

            for container_status in pod.status.container_statuses or []:
                state = container_status.state
                last_state = container_status.last_state

                containers.append(
                    {
                        "name": container_status.name,
                        "ready": container_status.ready,
                        "restart_count": container_status.restart_count,
                        "state": {
                            "waiting": (
                                {
                                    "reason": state.waiting.reason,
                                    "message": state.waiting.message,
                                }
                                if state.waiting
                                else None
                            ),
                            "running": (
                                {
                                    "started_at": state.running.started_at,
                                }
                                if state.running
                                else None
                            ),
                            "terminated": (
                                {
                                    "reason": state.terminated.reason,
                                    "message": state.terminated.message,
                                    "exit_code": state.terminated.exit_code,
                                    "started_at": state.terminated.started_at,
                                    "finished_at": state.terminated.finished_at,
                                }
                                if state.terminated
                                else None
                            ),
                        },
                        "last_state": {
                            "terminated": (
                                {
                                    "reason": last_state.terminated.reason,
                                    "message": last_state.terminated.message,
                                    "exit_code": last_state.terminated.exit_code,
                                    "started_at": last_state.terminated.started_at,
                                    "finished_at": last_state.terminated.finished_at,
                                }
                                if last_state.terminated
                                else None
                            ),
                        },
                    }
                )

            conditions = {}

            for condition in pod.status.conditions or []:
                conditions[condition.type] = {
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                    "last_transition_time": condition.last_transition_time,
                }

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="pod",
                    timestamp=datetime.now(timezone.utc),
                    namespace=pod.metadata.namespace,
                    resource=pod.metadata.name,
                    data={
                        "phase": pod.status.phase,
                        "pod_ip": pod.status.pod_ip,
                        "node_name": pod.spec.node_name,
                        "host_ip": pod.status.host_ip,
                        "start_time": pod.status.start_time,
                        "containers": containers,
                        "conditions": conditions,
                    },
                )
            )

        return evidence

    def collect_events(self) -> list[Evidence]:
        events = self.core_api.list_event_for_all_namespaces()

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
                    namespace=event.metadata.namespace,
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

    def collect_deployments(self) -> list[Evidence]:
        deployments = self.apps_api.list_deployment_for_all_namespaces()

        evidence = []

        for deployment in deployments.items:
            status = deployment.status
            spec = deployment.spec

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="deployment",
                    timestamp=datetime.now(timezone.utc),
                    namespace=deployment.metadata.namespace,
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

    def collect_services(self) -> list[Evidence]:
        services = self.core_api.list_service_for_all_namespaces()

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
                    namespace=service.metadata.namespace,
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

    def collect_nodes(self) -> list[Evidence]:
        nodes = self.core_api.list_node()

        evidence = []

        for node in nodes.items:
            conditions = {}

            for condition in node.status.conditions or []:
                conditions[condition.type] = condition.status

            evidence.append(
                Evidence(
                    source="kubernetes",
                    evidence_type="node",
                    timestamp=datetime.now(timezone.utc),
                    namespace=None,
                    resource=node.metadata.name,
                    data={
                        "ready": conditions.get("Ready"),
                        "memory_pressure": conditions.get("MemoryPressure"),
                        "disk_pressure": conditions.get("DiskPressure"),
                        "pid_pressure": conditions.get("PIDPressure"),
                        "unschedulable": node.spec.unschedulable or False,
                        "capacity_cpu": node.status.capacity.get("cpu"),
                        "capacity_memory": node.status.capacity.get("memory"),
                        "allocatable_cpu": node.status.allocatable.get("cpu"),
                        "allocatable_memory": node.status.allocatable.get(
                            "memory"
                        ),
                    },
                )
            )

        return evidence