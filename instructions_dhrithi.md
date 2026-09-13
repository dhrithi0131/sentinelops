# SENTINELOPS — DHRITHI DEVELOPMENT INSTRUCTIONS

## Owner

Dhrithi

## Role

Observability Infrastructure, Telemetry Ingestion, Persistence,
Remediation Infrastructure, API, Frontend, Deployment, and Production Engineering.

---

# 1. PROJECT MISSION

SentinelOps is an AI-powered Kubernetes Incident Time Machine.

The final system connects:

    Kubernetes
    Prometheus
    Loki
    Jaeger
    Incident Intelligence
    RAG
    Counterfactual Reasoning
    Safe Remediation
    Dashboard

Your responsibility is primarily the infrastructure and product layer
that allows Varsha's incident intelligence layer to operate reliably.

---

# 2. CURRENT BASELINE

Day 1 and Day 2 are complete.

Current important commit:

    c6baf5d feat: enrich Kubernetes evidence collection

Kubernetes collector currently supports:

- Pods
- Container states
- Container restarts
- Pod conditions
- Events
- Deployments
- Services
- Nodes

Current validation:

    4 tests passed

Current branch:

    day3-collaborator

Do NOT work directly on main.

---

# 3. FILE OWNERSHIP

Dhrithi owns:

    collectors/prometheus/
    collectors/loki/
    collectors/jaeger/
    telemetry/
    storage/
    remediation/
    backend/api/
    frontend/
    k8s/
    docs/deployment/

Varsha owns:

    models/
    correlation/
    incident_engine/
    rag/
    counterfactual/
    evaluation/
    docs/architecture/

Shared interfaces must be coordinated before modification.

---

# 4. IMPORTANT COLLABORATION PRINCIPLE

Your job is NOT to build a second SentinelOps.

Your job is to build the infrastructure that feeds and exposes
Varsha's intelligence layer.

Think:

    DHRITHI
        ↓
    DATA + INFRASTRUCTURE + API + UI
        ↓
    VARSHA
        ↓
    INTELLIGENCE

But both sides must remain independently testable.

---

# 5. DAY 3 — TELEMETRY INFRASTRUCTURE

Create:

    telemetry/

Possible structure:

    telemetry/
    ├── __init__.py
    ├── adapters.py
    └── registry.py

Responsibilities:

- telemetry source registration
- common ingestion interface
- source metadata
- timestamp handling
- normalization hooks

Do not duplicate Varsha's domain models.

---

# 6. DAY 4 — PROMETHEUS COLLECTOR

Create:

    collectors/prometheus/

Build:

    PrometheusCollector

Support:

    instant_query()
    range_query()
    query_pod_metrics()
    query_node_metrics()

Collect:

    CPU
    memory
    restarts
    network
    container metrics
    node metrics

Tests:

    tests/test_prometheus_collector.py

The collector should work against a configurable endpoint.

Do not hard-code localhost ports.

---

# 7. DAY 5 — LOKI COLLECTOR

Create:

    collectors/loki/

Build:

    LokiCollector

Support:

    query_logs()
    query_range()
    query_pod_logs()

Support:

    LogQL
    labels
    timestamps
    pod
    namespace
    container

Tests:

    tests/test_loki_collector.py

---

# 8. DAY 6 — JAEGER COLLECTOR

Create:

    collectors/jaeger/

Build:

    JaegerCollector

Support:

    search_traces()
    get_trace()
    extract_spans()

Represent:

    trace ID
    span ID
    service
    operation
    duration
    parent
    error

Tests:

    tests/test_jaeger_collector.py

---

# 9. DAY 7 — OBSERVABILITY INTEGRATION

Connect:

    Kubernetes
    Prometheus
    Loki
    Jaeger

into the telemetry infrastructure.

The output must satisfy the common telemetry contract.

Create integration tests using mocked responses where external services
are unavailable.

Do not require users to have all observability systems running just to
execute unit tests.

---

# 10. DAY 8 — INCIDENT INFRASTRUCTURE SUPPORT

Varsha owns incident detection.

Your responsibility:

    provide reliable telemetry access

The infrastructure must make it easy for detectors to request:

    metrics
    logs
    traces
    Kubernetes evidence

Do not put detection logic inside collectors.

Collectors collect.

Incident engine reasons.

---

# 11. DAY 9 — TIMELINE DATA ACCESS

Support Varsha's timeline engine with efficient retrieval.

Provide:

    time range
    entity
    source
    namespace
    resource

filtering.

Avoid repeatedly querying external systems unnecessarily.

---

# 12. DAY 10 — TELEMETRY STORAGE DESIGN

Create:

    storage/

Possible interfaces:

    EvidenceStore
    IncidentStore
    TimelineStore

Do not tightly couple domain logic to SQLite/PostgreSQL/etc.

Start simple.

The interface is more important than database complexity.

---

# 13. DAY 11 — PERSISTENCE IMPLEMENTATION

Implement the first persistent store.

Requirements:

    save
    get
    list
    search
    delete where appropriate

Support incident history.

Tests must prove data survives process restart.

---

# 14. DAY 12 — INCIDENT MEMORY STORAGE

Store:

    incident
    timeline
    DNA
    diagnosis
    resolution
    outcome

Varsha owns the domain models.

You own storage adapters.

Do not redefine the incident schema.

---

# 15. DAY 13 — SEARCH / FILTER INFRASTRUCTURE

Implement storage-level filtering for:

    timestamp
    namespace
    service
    severity
    incident type
    status

This will later support:

    dashboard
    RAG
    incident history
    evaluation

---

# 16. DAY 14 — VECTOR DATABASE INFRASTRUCTURE

Create:

    storage/vector/

Provide an abstraction:

    VectorStore

Support:

    upsert
    search
    delete
    metadata filtering

The rest of the project should not care which vector backend is used.

---

# 17. DAY 15 — INCIDENT MEMORY BACKEND

Connect the incident domain to persistence.

Flow:

    Incident
       ↓
    IncidentStore
       ↓
    Database

Tests:

    create incident
    save incident
    retrieve incident
    list incidents
    search incidents

---

# 18. DAY 16 — EMBEDDING INFRASTRUCTURE

Create:

    rag/embeddings/

Provide an embedding interface.

Requirements:

    deterministic test implementation
    configurable production implementation
    batch support where useful

Do not put API keys into source code.

---

# 19. DAY 17 — RAG SERVICE INFRASTRUCTURE

Varsha owns retrieval/diagnosis semantics.

You provide infrastructure:

    vector storage
    document storage
    embedding integration
    configuration

Support:

    incident documents
    runbooks
    technical documentation

---

# 20. DAY 18 — API FOUNDATION

Create:

    backend/api/

Expose clean APIs for:

    incidents
    timeline
    diagnosis
    evidence
    recommendations

Use typed request/response schemas.

Avoid returning raw Kubernetes API objects.

---

# 21. DAY 19 — API SAFETY

Implement:

    validation
    error responses
    request IDs
    structured logging
    authentication-ready architecture

Do not expose internal stack traces to clients.

---

# 22. DAY 20 — ACTION API CONTRACT

Create API support for:

    restart
    scale
    rollback
    patch

BUT:

The API must not allow arbitrary shell commands.

Allowed actions must be represented structurally.

Example:

    {
        "action": "scale",
        "target": "frontend",
        "replicas": 4
    }

---

# 23. DAY 21 — REMEDIATION EXECUTOR

Create:

    remediation/executor.py

Build:

    restart()
    scale()
    rollback()

Actions must target explicit Kubernetes resources.

No:

    os.system()
    arbitrary kubectl from LLM text
    shell=True execution of generated commands

---

# 24. DAY 22 — DRY-RUN SUPPORT

Every remediation action should support dry-run validation.

Example:

    validate scale frontend → 4

before:

    execute scale frontend → 4

Return structured results.

---

# 25. DAY 23 — REMEDIATION AUDIT LOG

Record:

    who requested action
    action
    target
    parameters
    approval
    timestamp
    result
    error if any

This is required for production-grade incident response.

---

# 26. DAY 24 — REMEDIATION SERVICE

Connect:

    API
      ↓
    Approval
      ↓
    Policy
      ↓
    Executor
      ↓
    Kubernetes

Varsha owns policy semantics.

You own execution infrastructure.

---

# 27. DAY 25 — FRONTEND FOUNDATION

Create frontend structure.

Recommended:

    frontend/

Provide:

    dashboard
    incidents
    incident detail
    timeline
    recommendations

Keep UI/API communication typed and documented.

---

# 28. DAY 26 — INCIDENT DASHBOARD

Build:

    cluster health
    active incidents
    severity
    incident status
    affected resources

Example:

    Nodes: 1
    Active incidents: 2
    Critical: 1

Do not hard-code dashboard values.

Use API data.

---

# 29. DAY 27 — INCIDENT DETAIL UI

Display:

    incident
    severity
    affected resource
    timeline
    evidence
    diagnosis
    confidence

Make the evidence inspectable.

---

# 30. DAY 28 — REMEDIATION UI

Display recommended actions:

    Restart
    Scale
    Rollback
    etc.

User must explicitly approve.

UI must clearly show:

    risk
    expected outcome
    confidence

No silent execution.

---

# 31. DAY 29 — INCIDENT REPLAY INFRASTRUCTURE

Support loading recorded incidents.

Provide API:

    GET /incidents/{id}
    GET /incidents/{id}/timeline
    GET /incidents/{id}/evidence

Frontend can then reconstruct historical incidents.

---

# 32. DAY 30 — TIME MACHINE UI

Build the visual timeline.

Required:

    timestamp axis
    event markers
    selected event
    evidence details

Example:

    10:30 ─── 10:31 ─── 10:32 ─── 10:33
                 ●
                 ↑
              selected

The user should be able to inspect what happened at each moment.

---

# 33. DAY 31 — OBSERVABILITY VISUALIZATION

Display:

    CPU
    memory
    restarts
    logs
    traces

when available.

Charts should align with the incident timeline.

This is one of the most impressive demo components.

---

# 34. DAY 32 — AI DIAGNOSIS UI

Display:

    ROOT CAUSE
    CONFIDENCE
    EVIDENCE
    SIMILAR INCIDENTS

Do not visually imply certainty when confidence is low.

Evidence should be clickable.

---

# 35. DAY 33 — COUNTERFACTUAL UI

Display:

    Action
    Predicted outcome
    Risk
    Confidence
    Historical support

Example:

    Scale → Low risk
    Restart → Medium risk
    Rollback → High impact

Human approval remains mandatory.

---

# 36. DAY 34 — FULL FRONTEND INTEGRATION

Connect:

    dashboard
    incidents
    timeline
    diagnosis
    RAG
    counterfactuals
    approval
    remediation
    verification

The UI must operate using real backend APIs.

No fake production data in the final demo.

---

# 37. DAY 35 — DOCKER + KUBERNETES DEPLOYMENT

Create:

    Dockerfile
    docker-compose where useful
    k8s/

Kubernetes:

    namespace.yaml
    backend-deployment.yaml
    backend-service.yaml
    configmap.yaml

Environment configuration must be externalized.

---

# 38. DAY 36 — FINAL PRODUCTION RELEASE

Own:

    deployment verification
    UI polish
    Docker build
    Kubernetes deployment
    screenshots
    demo environment
    final frontend testing

Work with Varsha on:

    end-to-end test
    final demo
    README
    presentation
    architecture

---

# 39. GIT RULES

Never work directly on main.

Before starting:

    git checkout main
    git pull origin main
    git checkout day3-collaborator
    git merge main

Before committing:

    python -m pytest -v
    git status

Commit:

    feat:
    fix:
    test:
    docs:
    refactor:

Example:

    feat: add Prometheus collector

Push:

    git push

Never:

    git push --force

---

# 40. PULL REQUEST RULE

Every completed feature goes:

    branch
      ↓
    tests
      ↓
    push
      ↓
    Pull Request
      ↓
    review
      ↓
    main

Do not merge another person's branch locally without coordination.

---

# 41. SHARED FILE RULE

If a file belongs to Varsha:

    ask before modifying it.

If a file belongs to Dhrithi:

    Varsha should not modify it without coordination.

For shared interfaces:

    discuss
    change contract
    test
    commit

Do not silently change API contracts.

---

# 42. QUALITY STANDARD

Every feature should include:

    implementation
    unit tests
    error handling
    type hints
    documentation
    integration test where appropriate

A working demo is not enough.

---

# 43. SECURITY STANDARD

Never:

- commit secrets
- commit API keys
- execute arbitrary LLM-generated shell
- bypass approval
- use force push
- disable safety checks
- fake telemetry
- fake evaluation metrics

Remediation must always be explicit and controlled.

---

# 44. INTERNSHIP-WORTHY ENGINEERING TARGET

Your work should demonstrate:

    Kubernetes
    Observability
    Prometheus
    Loki
    Jaeger
    Backend engineering
    API design
    Database design
    Vector search
    Docker
    Kubernetes deployment
    Frontend engineering
    Security
    Human-in-the-loop systems
    Production engineering

The important story is:

    telemetry
        ↓
    storage
        ↓
    API
        ↓
    intelligence
        ↓
    UI
        ↓
    approved remediation
        ↓
    verification

---

# 45. FINAL PRINCIPLE

Do not build isolated features.

Every feature must connect to the SentinelOps pipeline.

Your work should make Varsha's intelligence layer easier to consume,
while Varsha's intelligence should make your infrastructure useful.

The two halves must form one production-quality system.