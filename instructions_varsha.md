# SENTINELOPS — VARSHA DEVELOPMENT INSTRUCTIONS

## Owner

Varsha

## Role

Incident Intelligence, Evidence Correlation, RCA, RAG, Counterfactual Intelligence,
Safety Integration, Evaluation, and Final System Integration.

---

# 1. PROJECT MISSION

SentinelOps is an AI-powered Kubernetes Incident Time Machine.

The system must be capable of:

1. Observing Kubernetes infrastructure.
2. Collecting metrics, logs, traces, and Kubernetes state.
3. Normalizing telemetry.
4. Detecting incidents.
5. Constructing chronological incident timelines.
6. Identifying the earliest actionable anomaly.
7. Building incident dependency relationships.
8. Generating Incident DNA.
9. Classifying failures.
10. Detecting incident novelty.
11. Searching historical incidents.
12. Producing evidence-grounded root-cause analysis.
13. Generating counterfactual recovery strategies.
14. Predicting outcomes.
15. Recommending safe remediation.
16. Requiring human approval.
17. Executing controlled actions.
18. Verifying recovery.
19. Learning from previous incidents.
20. Providing a professional investigation dashboard.

The final system must feel like an engineering product, not a collection of scripts.

---

# 2. CURRENT BASELINE

Day 1 and Day 2 are complete.

Current important commit:

    c6baf5d feat: enrich Kubernetes evidence collection

Current Kubernetes collector supports:

- Pods
- Container state
- Container restarts
- Pod conditions
- Kubernetes events
- Deployments
- Services
- Nodes

Current validation:

    4 tests passed

Current branch:

    day3-varsha

Do NOT modify main directly.

---

# 3. BRANCH OWNERSHIP

Varsha works on:

    day3-varsha
    day4-varsha
    etc.

Dhrithi works on:

    day3-dhrithi
    day4-dhrithi
    etc.

However, because the project currently has:

    day3-varsha
    day3-collaborator

Dhrithi may initially use:

    day3-collaborator

Do not work directly on main.

---

# 4. GOLDEN RULE — FILE OWNERSHIP

Varsha owns the following major areas:

    models/
    correlation/
    incident_engine/
    rag/
    counterfactual/
    evaluation/
    docs/architecture/
    docs/evaluation/

Dhrithi owns the following major areas:

    collectors/prometheus/
    collectors/loki/
    collectors/jaeger/
    telemetry/
    storage/
    remediation/
    backend/api/
    frontend/
    k8s/

Shared files must be modified only when explicitly coordinated.

Never casually edit another person's module.

---

# 5. SHARED CONTRACT RULE

Before implementing a module, define its input/output contract.

Example:

    Collector
        ↓
    Evidence
        ↓
    Timeline
        ↓
    Incident
        ↓
    Diagnosis
        ↓
    Recommendation
        ↓
    Remediation
        ↓
    Verification

Each stage must communicate using typed models.

Do NOT pass random dictionaries between modules unless the schema explicitly allows it.

---

# 6. DAY 3 — KUBERNETES STATE NORMALIZATION

Goal:

Convert raw Kubernetes evidence into stable domain models.

Create:

    models/kubernetes.py

Possible models:

    PodSnapshot
    ContainerSnapshot
    NodeSnapshot
    DeploymentSnapshot
    ServiceSnapshot
    KubernetesEventSnapshot
    ContainerTermination

Responsibilities:

- Normalize Kubernetes collector output.
- Convert Kubernetes API objects into project-owned schemas.
- Preserve timestamps.
- Preserve namespace/resource identity.
- Preserve failure information.
- Make models serializable.

Do NOT rewrite the Kubernetes collector unless required for compatibility.

Tests:

    tests/test_kubernetes_models.py

Deliverable:

Raw Kubernetes state → normalized domain models.

---

# 7. DAY 4 — TELEMETRY CONTRACTS

Work with Dhrithi on the common telemetry interface.

Create:

    models/telemetry.py

Define common concepts:

    TelemetryEvent
    TelemetrySource
    EntityReference
    Severity
    MetricObservation
    LogObservation
    TraceObservation

Requirements:

- Every telemetry event has a timestamp.
- Every event has a source.
- Every event identifies an entity where possible.
- Every event contains structured metadata.

The model must support:

    Kubernetes
    Prometheus
    Loki
    Jaeger

Do not implement the external collectors here.

---

# 8. DAY 5 — PROMETHEUS DATA NORMALIZATION

Dhrithi owns the Prometheus collector.

Varsha owns normalization/integration.

Consume Prometheus data through the common telemetry contract.

Support:

- CPU
- Memory
- Restarts
- Network
- Container metrics
- Node metrics

Create tests for conversion into common telemetry.

Deliverable:

Prometheus observations can enter the unified evidence pipeline.

---

# 9. DAY 6 — LOKI DATA NORMALIZATION

Dhrithi owns Loki collection.

Varsha owns normalized log evidence.

Support:

- timestamps
- labels
- namespace
- pod
- container
- log message
- severity where available

Deliverable:

Loki logs can be compared with Kubernetes and metric evidence.

---

# 10. DAY 7 — JAEGER DATA NORMALIZATION

Dhrithi owns trace retrieval.

Varsha owns trace-to-evidence normalization.

Represent:

    Trace
      └── Span
            ├── service
            ├── operation
            ├── duration
            ├── error
            └── parent

Deliverable:

Traces participate in the unified timeline.

---

# 11. DAY 8 — INCIDENT DETECTION

Create:

    incident_engine/detector.py

Detect:

- CrashLoopBackOff
- OOMKilled
- Pending
- FailedScheduling
- readiness failures
- high CPU
- high memory
- application errors
- trace errors

Create detector interfaces rather than one giant function.

Example:

    BaseDetector
    KubernetesFailureDetector
    ResourceDetector
    ApplicationErrorDetector

Output:

    IncidentCandidate

Do not execute remediation here.

---

# 12. DAY 9 — INCIDENT TIMELINE

Create:

    incident_engine/timeline.py

Input:

    IncidentCandidate
    Evidence[]

Output:

    IncidentTimeline

Timeline entries must be chronologically ordered.

Support:

- Kubernetes events
- metrics
- logs
- traces

Example:

    10:31:02 Deployment updated
    10:31:05 Pod scheduled
    10:31:10 Memory spike
    10:31:12 Application error
    10:31:13 OOMKilled

The timeline is one of the project's core features.

---

# 13. DAY 10 — EARLIEST ACTIONABLE ANOMALY

Create:

    incident_engine/anomaly.py

The system must distinguish:

    symptom
    failure
    anomaly
    actionable anomaly

Example:

    OOMKilled
        ↑
    Memory limit exceeded
        ↑
    Memory continuously increasing
        ↑
    EARLIEST ACTIONABLE ANOMALY

Implement explainable scoring.

Do not use an opaque ML model unnecessarily.

---

# 14. DAY 11 — DEPENDENCY / CAUSAL GRAPH

Create:

    correlation/dependency_graph.py

Represent:

    Node
      ↓
    Pod
      ↓
    Container

And:

    Service
      ↓
    Endpoint

Also support application relationships.

Graph nodes should reference evidence/entities.

Deliverable:

Incident dependency graph.

---

# 15. DAY 12 — INCIDENT DNA

Create:

    incident_engine/dna.py

Incident DNA contains:

    trigger
    failure
    restart_pattern
    readiness
    affected_workload
    duration
    severity
    dependency information
    anomaly information

Example:

    {
        "trigger": "memory_growth",
        "failure": "OOMKilled",
        "restart_pattern": "repeated",
        "severity": "high"
    }

Incident DNA must be deterministic and serializable.

---

# 16. DAY 13 — FAILURE CLASSIFICATION

Create:

    incident_engine/classifier.py

Categories:

    Scheduling
    Resource
    Application
    Networking
    Dependency
    Configuration
    Infrastructure
    Unknown

Classification must include:

    category
    confidence
    evidence references
    explanation

---

# 17. DAY 14 — NOVELTY DETECTION

Create:

    incident_engine/novelty.py

Compare:

    current Incident DNA
        ↓
    historical Incident DNA

Output:

    novelty_score
    similar_incidents
    known_pattern

Do not build the vector database yet.

Use deterministic similarity initially.

---

# 18. DAY 15 — INCIDENT MEMORY

Varsha owns the incident domain model.

Create:

    models/incident.py

Represent:

    Incident
    IncidentDNA
    Timeline
    Diagnosis
    Resolution
    Outcome

Dhrithi owns the persistence implementation.

The domain model must remain storage-independent.

---

# 19. DAY 16 — VECTOR SEARCH CONTRACT

Define:

    rag/models.py

Represent:

    SearchDocument
    SearchResult
    EmbeddingRecord
    SimilarIncident

Do not hard-code the entire system to one vector database.

Use interfaces.

---

# 20. DAY 17 — RAG PIPELINE

Create:

    rag/retriever.py
    rag/pipeline.py

Pipeline:

    Query
      ↓
    Retriever
      ↓
    Historical incidents
      +
    Runbooks
      ↓
    Context
      ↓
    Diagnosis

RAG must return source references.

---

# 21. DAY 18 — EVIDENCE-GROUNDED RCA

Create:

    incident_engine/diagnosis.py

Output:

    root_cause
    confidence
    evidence
    timeline_references
    similar_incidents
    explanation

Critical rule:

NO EVIDENCE = NO CLAIM.

If evidence is insufficient:

    "Insufficient evidence"

must be a valid result.

---

# 22. DAY 19 — AI GUARDRAILS

Create:

    rag/guardrails.py

Every generated claim should be traceable to evidence.

Implement:

    evidence validation
    confidence thresholds
    unsupported-claim detection
    citation/reference validation

The LLM must not invent Kubernetes events, metrics, logs, traces, or historical incidents.

---

# 23. DAY 20 — ACTION MODEL

Create:

    counterfactual/actions.py

Represent:

    RestartPod
    ScaleDeployment
    RollbackDeployment
    IncreaseMemoryLimit
    IncreaseReplicas
    PauseRollout

Each action must contain:

    target
    parameters
    expected effect
    risk level

No execution here.

---

# 24. DAY 21 — COUNTERFACTUAL ENGINE

Create:

    counterfactual/simulator.py

Start rule-based.

Example:

    memory increase
        ↓
    lower OOM probability

Do not pretend to have a real Kubernetes world model.

Predictions must state assumptions.

---

# 25. DAY 22 — OUTCOME PREDICTION

Create:

    counterfactual/predictor.py

Output:

    action
    predicted outcome
    risk
    confidence
    assumptions
    evidence

Actions should be ranked.

---

# 26. DAY 23 — HISTORICAL COUNTERFACTUAL LEARNING

Combine:

    historical incidents
    +
    similar Incident DNA
    +
    previous outcomes
    +
    counterfactual action

Example:

    "3 similar incidents improved after scaling."

This evidence must be explicitly referenced.

---

# 27. DAY 24 — DECISION ENGINE

Create:

    counterfactual/decision.py

Pipeline:

    Incident
       ↓
    Candidate actions
       ↓
    Risk
       ↓
    Historical evidence
       ↓
    Expected outcome
       ↓
    Recommendation

Return:

    recommended_action
    confidence
    reasons
    evidence
    risk

---

# 28. DAY 25 — HUMAN APPROVAL CONTRACT

Create:

    remediation/approval.py

Represent:

    ApprovalRequest
    ApprovalDecision
    ApprovalPolicy

No AI action should directly execute arbitrary commands.

---

# 29. DAY 26 — REMEDIATION INTEGRATION

Dhrithi owns Kubernetes execution.

Varsha owns decision-to-action integration.

The system must only execute known action types.

Never execute arbitrary shell generated by an LLM.

---

# 30. DAY 27 — SAFETY POLICY INTEGRATION

Varsha owns policy semantics.

Required concepts:

    allowlist
    validation
    dry-run
    approval
    audit

Dangerous actions must be rejected.

---

# 31. DAY 28 — VERIFICATION LOGIC

Create:

    incident_engine/verification.py

After remediation:

    action
      ↓
    wait
      ↓
    collect telemetry
      ↓
    compare incident state
      ↓
    resolved / unresolved

Verification must be evidence based.

---

# 32. DAY 29 — INCIDENT EVALUATION

Create:

    evaluation/incidents/

Test scenarios:

    CrashLoopBackOff
    OOMKilled
    FailedScheduling
    Readiness failure
    CPU saturation
    Dependency timeout

Each test should define:

    expected root cause
    expected evidence
    expected timeline
    expected classification

---

# 33. DAY 30 — INCIDENT REPLAY CONTRACT

Create:

    evaluation/replay.py

Replay should reconstruct:

    t0
    t1
    t2
    t3
    ...

The replay system must use recorded evidence rather than fake claims.

---

# 34. DAY 31 — EVALUATION FRAMEWORK

Create:

    evaluation/metrics.py

Measure:

    detection latency
    RCA accuracy
    earliest anomaly accuracy
    retrieval quality
    counterfactual accuracy
    remediation success

Produce machine-readable results.

---

# 35. DAY 32 — FRONTEND INTEGRATION

Dhrithi owns frontend implementation.

Varsha owns:

    API contracts
    incident response schemas
    diagnosis schemas
    timeline schemas

UI must display:

    incidents
    timeline
    root cause
    evidence
    confidence
    similar incidents
    counterfactuals

---

# 36. DAY 33 — INCIDENT TIME MACHINE

Varsha owns backend timeline semantics.

Dhrithi owns visual UI.

Required interactions:

    timeline
    event selection
    timestamp inspection
    evidence inspection
    incident state

This is the hero feature.

---

# 37. DAY 34 — AI DIAGNOSIS UI

Varsha provides stable API contracts.

Dhrithi renders:

    ROOT CAUSE
    CONFIDENCE
    EVIDENCE
    SIMILAR INCIDENTS
    COUNTERFACTUALS
    RECOMMENDATION

Every AI claim should expose evidence.

---

# 38. DAY 35 — PRODUCTION INTEGRATION

Dhrithi owns:

    Docker
    Kubernetes deployment
    configuration wiring

Varsha owns:

    integration testing
    safety checks
    end-to-end pipeline verification

Required:

    backend starts
    collectors connect
    incident detection works
    RCA works
    recommendation works
    approval works
    verification works

---

# 39. DAY 36 — FINAL RELEASE

Both developers work together.

Varsha owns:

    evaluation
    architecture documentation
    RCA demonstration
    incident replay
    final technical verification

Dhrithi owns:

    UI polish
    deployment verification
    screenshots
    demo environment

Both:

    README
    demo
    presentation
    GitHub cleanup
    tests
    documentation

---

# 40. DEFINITION OF DONE

A feature is NOT complete merely because the code runs.

Every feature should have:

    implementation
    tests
    type-safe interface
    documentation
    error handling
    integration test where applicable
    Git commit

---

# 41. GIT RULES

Before starting work:

    git checkout main
    git pull origin main
    git checkout day3-varsha
    git merge main

Do NOT use:

    git push --force

Do NOT rewrite another person's branch.

Before every push:

    python -m pytest -v
    git status

Commit format:

    feat:
    fix:
    test:
    docs:
    refactor:

Example:

    feat: add incident timeline engine

---

# 42. INTEGRATION RULE

A branch is integrated only through Pull Request.

Never manually copy files between branches.

Flow:

    feature branch
        ↓
    tests
        ↓
    push
        ↓
    Pull Request
        ↓
    review
        ↓
    merge into main

After merging:

    git checkout main
    git pull origin main

Then update your working branch.

---

# 43. NEVER DO THIS

Do not:

- modify main directly
- force push
- overwrite Dhrithi's files
- rewrite shared models without coordination
- commit .venv
- commit secrets
- put API keys in code
- allow arbitrary LLM shell execution
- skip tests
- merge untested code
- fake evaluation metrics

---

# 44. INTERNSHIP-WORTHY STANDARD

SentinelOps should demonstrate:

    Kubernetes
    Observability
    Python backend engineering
    Distributed systems
    Incident response
    AI/RAG
    Explainable AI
    Causal reasoning
    Safe agentic systems
    Testing
    Docker
    Kubernetes deployment
    Frontend engineering
    Evaluation

The project should be explainable in an interview from:

    telemetry
        ↓
    evidence
        ↓
    incident
        ↓
    timeline
        ↓
    DNA
        ↓
    RCA
        ↓
    RAG
        ↓
    counterfactual
        ↓
    recommendation
        ↓
    human approval
        ↓
    remediation
        ↓
    verification
        ↓
    learning

---

# 45. FINAL PRINCIPLE

Do not optimize for number of files.

Optimize for:

    correctness
    architecture
    explainability
    safety
    reproducibility
    measurable results

The final project must be something that can be demonstrated live
and defended technically during an internship interview.