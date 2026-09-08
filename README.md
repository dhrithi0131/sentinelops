# SentinelOps

## Day 0 — Kubernetes & Observability Foundation

Date: 08 September 2026

### Kubernetes
- Docker Desktop + Minikube
- Kubernetes cluster and node health
- Namespaces
- Pods, Deployments and StatefulSets
- Pod lifecycle and states
- Resource requests, limits and actual usage
- Scheduler and Pending Pods
- FailedScheduling
- CrashLoopBackOff
- OOMKilled
- Eviction concepts
- Kubernetes Events
- Readiness, liveness and startup probe concepts

### Networking
- Services
- Selectors
- EndpointSlices
- CoreDNS
- Kubernetes Service DNS
- Pod ? Service ? Pod communication

### Observability
- Metrics Server
- Prometheus
- Grafana
- Loki
- Promtail
- Jaeger
- Kubernetes state + metrics + logs + traces correlation

### Incident Experiments
1. CrashLoopBackOff / process failure
2. CPU stress
3. OOMKilled
4. Pending Pod / FailedScheduling
5. Readiness probe failure
6. Distributed trace with HotROD
7. Redis timeout observed inside a distributed trace

### Key Day 0 Insight

A Kubernetes system cannot be understood from a single signal.

SentinelOps will eventually correlate:

Kubernetes state + Events + Metrics + Logs + Traces

to reconstruct how an incident evolved over time and identify the earliest actionable anomaly.

## Day 0 Status

COMPLETE
