/* SentinelOps frontend controller */
(() => {
    "use strict";

    const $ = (selector, root = document) =>
        root.querySelector(selector);

    const $$ = (selector, root = document) =>
        [...root.querySelectorAll(selector)];

    const state = {
        page: "overview",
        selectedIncident: "INC-2407",
        incidents: [],
        timeline: [],
        recommendations: [],
        evidence: [],
        diagnosis: null,
        similarIncidents: [],
        toastTimer: null
    };

    const demoIncidents = [
        {
            id: "INC-2407",
            title: "API latency spike",
            severity: "CRITICAL",
            service: "api-gateway",
            namespace: "production",
            description:
                "Elevated p95 latency detected on production API workloads.",
            status: "Investigating",
            timestamp: "08:42"
        },
        {
            id: "INC-2406",
            title: "Memory pressure",
            severity: "WARNING",
            service: "worker-pool",
            namespace: "production",
            description:
                "Memory utilization above threshold on worker nodes.",
            status: "Monitoring",
            timestamp: "08:36"
        },
        {
            id: "INC-2405",
            title: "Pod restart detected",
            severity: "MINOR",
            service: "payments",
            namespace: "production",
            description:
                "Payment service restarted after a failed health check.",
            status: "Open",
            timestamp: "08:21"
        }
    ];

    const demoTimeline = {
        "INC-2407": [
            {
                timestamp: "08:42",
                source: "Prometheus",
                event: "API latency anomaly detected",
                details:
                    "p95 latency crossed the configured service threshold."
            },
            {
                timestamp: "08:44",
                source: "Alertmanager",
                event: "Critical incident created",
                details:
                    "An alert was grouped and routed to the operations queue."
            },
            {
                timestamp: "08:45",
                source: "Loki",
                event: "Upstream request timeouts observed",
                details:
                    "Timeout messages increased in api-gateway logs."
            },
            {
                timestamp: "08:49",
                source: "SentinelOps",
                event: "Diagnosis generated",
                details:
                    "The gateway and upstream dependency are recommended for investigation."
            }
        ],

        "INC-2406": [
            {
                timestamp: "08:36",
                source: "Prometheus",
                event: "Memory threshold exceeded",
                details:
                    "Worker memory usage exceeded the warning threshold."
            },
            {
                timestamp: "08:38",
                source: "Kubernetes",
                event: "Pod resource pressure detected",
                details:
                    "One or more worker pods are approaching their memory limit."
            }
        ],

        "INC-2405": [
            {
                timestamp: "08:21",
                source: "Kubernetes",
                event: "Container restart detected",
                details:
                    "A payment pod restarted after failing a health check."
            },
            {
                timestamp: "08:22",
                source: "SentinelOps",
                event: "Incident opened",
                details: "Workload health is being monitored."
            }
        ]
    };

    const demoRecommendations = [
        {
            title: "Inspect upstream dependency health",
            description:
                "Review upstream latency and timeout rates before changing gateway capacity.",
            action: "inspect_dependency",
            risk: "Low"
        },
        {
            title: "Restart unhealthy gateway pod",
            description:
                "Use only if pod-level evidence confirms a stuck or unhealthy gateway process.",
            action: "restart_pod",
            risk: "Medium"
        },
        {
            title: "Scale gateway deployment",
            description:
                "Consider adding replicas if saturation persists and cluster capacity is available.",
            action: "scale_deployment",
            risk: "Medium"
        }
    ];

    const demoLogs = [
        {
            time: "08:49:12",
            level: "ERROR",
            service: "api-gateway",
            message: "Upstream request timed out after 3000ms"
        },
        {
            time: "08:48:57",
            level: "WARN",
            service: "worker-pool",
            message: "Memory utilization reached 82 percent"
        },
        {
            time: "08:48:21",
            level: "INFO",
            service: "payments",
            message: "Health check completed successfully"
        },
        {
            time: "08:47:42",
            level: "ERROR",
            service: "api-gateway",
            message: "Retry budget exceeded for upstream request"
        },
        {
            time: "08:46:11",
            level: "INFO",
            service: "catalog",
            message: "Cache refresh completed"
        },
        {
            time: "08:45:02",
            level: "WARN",
            service: "worker-pool",
            message: "Container approaching memory request threshold"
        }
    ];

    /* --------------------------------------------------
       HELPERS
    -------------------------------------------------- */

    function safe(value) {
        return String(value ?? "").replace(/[&<>"']/g, character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[character]);
    }

    function incidentId(item) {
        return item?.id
            ?? item?.incident_id
            ?? item?.incidentId
            ?? item?.key
            ?? "INC-UNKNOWN";
    }

    function severityOf(item) {
        return String(
            item?.severity ?? item?.level ?? "WARNING"
        ).toUpperCase();
    }

    function titleOf(item) {
    return item?.title
        ?? item?.metadata?.title
        ?? item?.metadata?.description
        ?? item?.description
        ?? item?.summary
        ?? item?.incident_id
        ?? item?.id
        ?? "Untitled incident";
    }

    function serviceOf(item) {
    return item?.service
        ?? item?.service_name
        ?? item?.workload
        ?? item?.metadata?.service
        ?? item?.metadata?.affected_workload
        ?? "unknown-service";
    }

    function descriptionOf(item) {
        return item?.description
            ?? item?.message
            ?? item?.summary
            ?? "No description provided by the incident source.";
    }

    function notify(message) {
        const toast = $("#toast");

        if (!toast) return;

        toast.textContent = message;
        toast.classList.add("show");

        clearTimeout(state.toastTimer);

        state.toastTimer = setTimeout(() => {
            toast.classList.remove("show");
        }, 3200);
    }

    /* --------------------------------------------------
       PAGE NAVIGATION
    -------------------------------------------------- */

    function goToPage(page) {
        if (!$(`#page-${page}`)) return;

        state.page = page;

        $$(".page").forEach(section => {
            section.classList.toggle(
                "active",
                section.dataset.pageSection === page
            );
        });

        $$(".nav-item").forEach(button => {
            button.classList.toggle(
                "active",
                button.dataset.page === page
            );
        });

        const pageTitle =
            page.charAt(0).toUpperCase() + page.slice(1);

        $("#breadcrumbTitle").textContent = pageTitle;
        document.title = `SentinelOps — ${pageTitle}`;

        closeMobileNav();

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }

    function closeMobileNav() {
        $("#sidebar").classList.remove("mobile-open");
        $("#sidebarScrim").classList.remove("visible");
    }

    /* --------------------------------------------------
       INCIDENTS
    -------------------------------------------------- */

    function renderIncidentRow(item, selected = false) {
        const id = incidentId(item);
        const severity = severityOf(item);

        return `
            <button
                type="button"
                class="incident-row ${selected ? "selected" : ""}"
                data-incident-id="${safe(id)}"
            >
                <span class="severity-mark ${safe(severity)}"></span>

                <span class="incident-copy">
                    <strong>${safe(titleOf(item))}</strong>
                    <small>
                        ${safe(id)} ·
                        ${safe(serviceOf(item))} ·
                        ${safe(item.namespace ?? "production")}
                    </small>
                </span>

                <span class="severity-label ${safe(severity)}">
                    ${safe(severity)}
                </span>
            </button>
        `;
    }

    function renderIncidents() {
        const searchQuery =
            ($("#incidentSearch")?.value ?? "").toLowerCase();

        const severityFilter =
            $("#severityFilter")?.value ?? "all";

        const visibleIncidents = state.incidents.filter(item => {
            const searchableText = [
                incidentId(item),
                titleOf(item),
                serviceOf(item),
                item.namespace,
                descriptionOf(item)
            ].join(" ").toLowerCase();

            const matchesSearch =
                searchableText.includes(searchQuery);

            const matchesSeverity =
                severityFilter === "all"
                || severityOf(item) === severityFilter;

            return matchesSearch && matchesSeverity;
        });

        $("#incidentList").innerHTML = visibleIncidents.length
            ? visibleIncidents.map(item =>
                renderIncidentRow(
                    item,
                    incidentId(item) === state.selectedIncident
                )
            ).join("")
            : `<div class="empty-state">
                No incidents match your filters.
               </div>`;

        $("#overviewIncidentList").innerHTML =
            state.incidents.slice(0, 3).map(item =>
                renderIncidentRow(
                    item,
                    incidentId(item) === state.selectedIncident
                )
            ).join("");

        $("#activeIncidentStat").textContent =
            state.incidents.length;

        $("#criticalStat").textContent =
            state.incidents.filter(
                item => severityOf(item) === "CRITICAL"
            ).length;

        $("#incidentNavCount").textContent =
            state.incidents.length;

        $("#incidentQueueCount").textContent =
            `${visibleIncidents.length} incident${visibleIncidents.length === 1 ? "" : "s"}`;

        $("#incidentQueueSubtitle").textContent =
            `${visibleIncidents.length} incident${visibleIncidents.length === 1 ? "" : "s"} in queue`;

        $("#metricsAlertCount").textContent =
            state.incidents.length;

        renderIncidentDetails();
    }

    function renderIncidentDetails() {
        const item = state.incidents.find(
            incident =>
                incidentId(incident) === state.selectedIncident
        );

        if (!item) {
            $("#incidentDetails").innerHTML = `
                <div class="empty-state">
                    Select an incident to view its details.
                </div>
            `;
            return;
        }

        $("#incidentDetails").innerHTML = `
            <div class="detail-block">
                <h3>Incident ID</h3>
                <p>${safe(incidentId(item))}</p>
            </div>

            <div class="detail-block">
                <h3>Title</h3>
                <p>${safe(titleOf(item))}</p>
            </div>

            <div class="detail-block">
                <h3>Severity</h3>
                <p>
                    <span class="severity-label ${safe(severityOf(item))}">
                        ${safe(severityOf(item))}
                    </span>
                </p>
            </div>

            <div class="detail-block">
                <h3>Service / workload</h3>
                <p>${safe(serviceOf(item))}</p>
            </div>

            <div class="detail-block">
                <h3>Namespace</h3>
                <p>${safe(item.namespace ?? "production")}</p>
            </div>

            <div class="detail-block">
                <h3>Status</h3>
                <p>${safe(item.status ?? item.state ?? "Open")}</p>
            </div>

            <div class="detail-block">
                <h3>Description</h3>
                <p>${safe(descriptionOf(item))}</p>
            </div>

            <button
                class="secondary-button"
                id="viewIncidentTimeline"
                type="button"
            >
                View incident timeline →
            </button>
                        
            <div class="detail-block">
                <h3>Similar incidents (RAG)</h3>
                ${
                    (state.similarIncidents ?? []).length > 0
                        ? state.similarIncidents.map(match => `
                            <div class="similar-incident-row">
                                <strong>${safe(match.incident_id ?? match.id ?? "Unknown incident")}</strong>
                                <span>Similarity: ${(Number(match.similarity_score ?? 0) * 100).toFixed(1)}%</span>
                            </div>
                        `).join("")
                        : `<p>No similar incidents found.</p>`
                }
            </div>

        `;

        $("#viewIncidentTimeline")?.addEventListener("click", () => {
            populateTimelineSelect();
            goToPage("timeline");
            renderTimeline();
        });
    }

    /* --------------------------------------------------
       TIMELINE
    -------------------------------------------------- */

    function normalizeEvents(data) {
        if (Array.isArray(data)) return data;
        if (Array.isArray(data?.timeline)) return data.timeline;
        if (Array.isArray(data?.events)) return data.events;
        if (Array.isArray(data?.items)) return data.items;

        return [];
    }

    function populateTimelineSelect() {
        const select = $("#timelineIncidentSelect");

        select.innerHTML = state.incidents.map(item => {
            const id = incidentId(item);

            return `
                <option
                    value="${safe(id)}"
                    ${id === state.selectedIncident ? "selected" : ""}
                >
                    ${safe(id)} — ${safe(titleOf(item))}
                </option>
            `;
        }).join("");
    }

    function renderTimeline() {
        const selectValue =
            $("#timelineIncidentSelect")?.value;

        const id = selectValue || state.selectedIncident;

        const events = state.timeline.length
            ? state.timeline
            : (demoTimeline[id] || []);

        $("#timelineCount").textContent =
            `${events.length} events`;

        $("#timelineContent").innerHTML = events.length
            ? events.map(event => `
                <div class="timeline-item">
                    <div class="timeline-marker"></div>

                    <div class="timeline-body">
                        <div class="timeline-meta">
                            <span>${safe(event.source ?? event.type ?? "EVENT")}</span>
                            <time>
                                ${safe(event.timestamp ?? event.time ?? event.created_at ?? "—")}
                            </time>
                        </div>

                        <strong>
                            ${safe(event.event ?? event.title ?? event.message ?? event.name ?? "Incident event")}
                        </strong>

                        <p>
                            ${safe(event.details ?? event.description ?? event.message ?? "")}
                        </p>
                    </div>
                </div>
            `).join("")
            : `
                <div class="empty-state">
                    No timeline events are available for this incident.
                </div>
            `;
    }

    /* --------------------------------------------------
       RECOMMENDATIONS AND DIAGNOSIS
    -------------------------------------------------- */

    function renderRecommendations() {
        const recommendations =
            Array.isArray(state.recommendations)
                ? state.recommendations
                : [];

        $("#recommendationsContent").innerHTML =
            recommendations.length
                ? recommendations.map((recommendation, index) => `
                    <div class="recommendation-card">
                        <small>
                            Risk: ${safe(
                    recommendation.risk
                    ?? recommendation.priority
                    ?? "Suggested action"
                )}
                        </small>

                        <strong>
                            ${safe(
                    recommendation.title
                    ?? recommendation.name
                    ?? recommendation.action
                    ?? `Recommendation ${index + 1}`
                )}
                        </strong>

                        <p>
                            ${safe(
                    recommendation.description
                    ?? recommendation.reason
                    ?? recommendation.details
                    ?? "Review this recommendation with the incident evidence before proceeding."
                )}
                        </p>

                        <button
                            type="button"
                            class="recommendation-select"
                            data-recommendation="${index}"
                            data-action="${safe(
                    recommendation.action
                    ?? recommendation.action_type
                    ?? "restart_pod"
                )}"
                        >
                            Use this action
                        </button>
                    </div>
                `).join("")
                : `
                    <div class="empty-state">
                        No recommendations returned for this incident.
                    </div>
                `;

        $("#recommendationSubtitle").textContent =
            `Suggestions for ${state.selectedIncident}`;
    }

    function renderActivity() {
        const events = state.timeline.length
            ? state.timeline.slice(0, 4)
            : (demoTimeline["INC-2407"] || []);

        $("#overviewActivityList").innerHTML = events.length
            ? events.map(event => `
                <div class="activity-item">
                    <span class="activity-icon">◷</span>

                    <div>
                        <strong>
                            ${safe(event.event ?? event.title ?? event.message ?? "Operational event")}
                        </strong>

                        <p>
                            ${safe(event.source ?? event.type ?? "SentinelOps")}
                            ·
                            ${safe(event.details ?? event.description ?? "")}
                        </p>
                    </div>

                    <time>
                        ${safe(event.timestamp ?? event.time ?? "")}
                    </time>
                </div>
            `).join("")
            : `<div class="empty-state">No recent activity available.</div>`;
    }

    /* --------------------------------------------------
       LOGS AND METRICS CHART
    -------------------------------------------------- */

    function renderLogs() {
        const query =
            ($("#logSearch")?.value ?? "").toLowerCase();

        const level =
            $("#logLevelFilter")?.value ?? "all";

        const rows = demoLogs.filter(log => {
            const text = [
                log.time,
                log.level,
                log.service,
                log.message
            ].join(" ").toLowerCase();

            return text.includes(query)
                && (level === "all" || log.level === level);
        });

        $("#logsTable").innerHTML = rows.map(log => `
            <tr>
                <td>${safe(log.time)}</td>
                <td>
                    <span class="log-level ${safe(log.level)}">
                        ${safe(log.level)}
                    </span>
                </td>
                <td>${safe(log.service)}</td>
                <td>${safe(log.message)}</td>
            </tr>
        `).join("");

        $("#logCount").textContent =
            `${rows.length} records`;
    }

    function renderChart() {
        const values = [
            42, 56, 49, 66, 61, 74,
            68, 57, 82, 72, 64, 78,
            61, 69, 87, 73, 66, 80
        ];

        $("#throughputChart").innerHTML =
            values.map((value, index) => `
                <div
                    class="chart-bar"
                    title="${value * 20} requests/s"
                    style="
                        height: ${value}%;
                        animation-delay: ${index * 25}ms;
                    "
                ></div>
            `).join("");
    }

    /* --------------------------------------------------
       API REQUEST HANDLING
    -------------------------------------------------- */

    async function apiCall(functionName, ...args) {
        const apiFunction = window[functionName];

        if (typeof apiFunction !== "function") {
            return null;
        }

        try {
            return await apiFunction(...args);
        } catch (error) {
            console.warn(`${functionName} failed:`, error);

            return {
                __error: error.message || String(error)
            };
        }
    }

    async function selectIncident(id) {
        if (!id) return;
        state.selectedIncident = id;
        await loadIncidentData(id);
    }

    async function loadIncidentData(id) {
        const results = await Promise.all([
            typeof getIncident === "function"
                ? getIncident(id).catch(e => ({ __error: e.message }))
                : apiCall("getIncident", id),
            typeof getTimeline === "function"
                ? getTimeline(id).catch(e => ({ __error: e.message }))
                : apiCall("getTimeline", id),
            typeof getEvidence === "function"
                ? getEvidence(id).catch(e => ({ __error: e.message }))
                : apiCall("getEvidence", id),
            typeof getRecommendations === "function"
                ? getRecommendations(id).catch(e => ({ __error: e.message }))
                : apiCall("getRecommendations", id),
            typeof getDiagnosis === "function"
                ? getDiagnosis(id).catch(e => ({ __error: e.message }))
                : apiCall("getDiagnosis", id),
            typeof window.getSimilarIncidents === "function"
                ? window.getSimilarIncidents(id).catch(e => ({ __error: e.message }))
                : Promise.resolve({ retrieved_incidents: [] })    
              
        ]);

        const [
            incident,
            timeline,
            evidence,
            recommendations,
            diagnosis,
            similarIncidents
        ] = results;

        if (incident && !incident.__error) {
            const normalized =
                incident.incident ?? incident.data ?? incident;

            const foundIndex = state.incidents.findIndex(
                item => incidentId(item) === id
            );

            const normalizedId = incidentId(normalized);

            const item = {
                ...normalized,
                id: normalizedId === "INC-UNKNOWN"
                    ? id
                    : normalizedId
            };

            if (foundIndex >= 0) {
                state.incidents[foundIndex] = {
                    ...state.incidents[foundIndex],
                    ...item
                };
            } else {
                state.incidents.unshift(item);
            }
        }

        state.timeline =
            timeline && !timeline.__error
                ? normalizeEvents(timeline)
                : (demoTimeline[id] || []);

        state.evidence =
            evidence && !evidence.__error
                ? (
                    Array.isArray(evidence)
                        ? evidence
                        : evidence.items ?? evidence.evidence ?? []
                )
                : [];

        state.recommendations =
            recommendations && !recommendations.__error
                ? (
                    Array.isArray(recommendations)
                        ? recommendations
                        : recommendations.recommendations
                        ?? recommendations.items
                        ?? []
                )
                : demoRecommendations;

        state.diagnosis =
            diagnosis && !diagnosis.__error
                ? diagnosis
                : null;
            state.similarIncidents = similarIncidents?.retrieved_incidents ?? [];    

        renderIncidents();
        populateTimelineSelect();
        renderTimeline();
        renderRecommendations();
        renderActivity();
    }


    async function loadIncidents() {
        try {
            const apiFunction =
                window.getIncidents ||
                (typeof getIncidents === "function" ? getIncidents : null);

            if (!apiFunction) {
                throw new Error("Incident API is unavailable.");
            }

            const liveIncidents = await apiFunction();

            if (!Array.isArray(liveIncidents)) {
                throw new Error("Incident API returned an invalid response.");
            }

            // Use the incidents returned by the backend, even if the list is empty.
            state.incidents = liveIncidents;

        } catch (error) {
            console.error("Could not load incidents from API:", error);

            // Do not load demo incidents into the live dashboard.
            state.incidents = [];
        }

        const ids = state.incidents.map(incidentId);

        await Promise.all(
            ids.map(id => loadIncidentData(id))
        );

        renderIncidents();
        populateTimelineSelect();
        renderTimeline();
        renderRecommendations();
        renderActivity();
    }


    /* --------------------------------------------------
       REMEDIATION
    -------------------------------------------------- */

    const SUPPORTED_ACTIONS = [
        "restart_pod",
        "scale_deployment",
        "rollback_deployment",
        "clear_cache"
    ];

    function getRemediationAction() {
        const actionSelect = $("#remediationAction");
        const action = actionSelect ? actionSelect.value : "";

        if (!SUPPORTED_ACTIONS.includes(action)) {
            throw new Error(`Unsupported remediation action: ${action}`);
        }

        const target = ($("#remediationTarget")?.value || "").trim();
        const reason = ($("#remediationReason")?.value || "").trim();

        const actionTypeMap = {
            "restart_pod": "restart",
            "scale_deployment": "scale",
            "rollback_deployment": "rollback",
            "clear_cache": "restart"
        };

        const incident = state.incidents.find(
            item => incidentId(item) === state.selectedIncident
        );
        const namespace = incident?.namespace || "production";

        return {
            action_type: actionTypeMap[action] || action,
            resource_type: "deployment",
            namespace: namespace,
            resource_name: target,
            parameters: action === "scale_deployment" ? { replicas: 3 } : {},
            action: action,
            target: target,
            reason: reason,
            incident_id: state.selectedIncident
        };
    }

    function getRemediationPayload() {
        return getRemediationAction();
    }

    async function runDryRun() {
        const result = $("#remediationResult");
        let payload;
        try {
            payload = getRemediationAction();
        } catch (error) {
            result.className = "result-box error";
            result.textContent = error.message;
            return;
        }

        if (!payload.resource_name) {
            result.className = "result-box error";
            result.textContent =
                "Enter a target resource before running the dry-run.";
            return;
        }

        result.className = "result-box";
        result.textContent = "Running dry-run…";

        const apiPayload = {
            action_type: payload.action_type,
            resource_type: payload.resource_type,
            namespace: payload.namespace,
            resource_name: payload.resource_name,
            parameters: payload.parameters,
            dry_run: true
        };

        const response = typeof dryRunRemediation === "function"
            ? await dryRunRemediation(apiPayload).catch(e => ({ __error: e.message }))
            : await apiCall("dryRunRemediation", apiPayload);

        if (response === null) {
            result.className = "result-box";

            result.textContent =
                "Demo dry-run prepared.\n"
                + `Incident: ${payload.incident_id}\n`
                + `Action: ${payload.action}\n`
                + `Target: ${payload.resource_name}\n`
                + "No changes were applied. Configure api.js/backend connectivity to run a real dry-run.";

            return;
        }

        if (response.__error) {
            result.className = "result-box error";
            result.textContent =
                `Dry-run failed: ${response.__error}`;
            return;
        }

        result.className = "result-box success";
        result.textContent =
            `Dry-run response:\n${JSON.stringify(response, null, 2)}`;
    }

    async function executeAction(event) {
        if (event && event.preventDefault) {
            event.preventDefault();
        }

        const result = $("#remediationResult");
        let payload;
        try {
            payload = getRemediationAction();
        } catch (error) {
            result.className = "result-box error";
            result.textContent = error.message;
            return;
        }

        if (!payload.resource_name) {
            result.className = "result-box error";
            result.textContent =
                "Enter a target resource before execution.";
            return;
        }

        const confirmed = window.confirm(
            `Execute "${payload.action}" against "${payload.resource_name}" `
            + `for ${payload.incident_id}? This may change your environment.`
        );

        if (!confirmed) return;

        result.className = "result-box";
        result.textContent = "Sending remediation request…";

        const apiPayload = {
            action_type: payload.action_type,
            resource_type: payload.resource_type,
            namespace: payload.namespace,
            resource_name: payload.resource_name,
            parameters: payload.parameters
        };

        const response = typeof executeRemediation === "function"
            ? await executeRemediation(apiPayload).catch(e => ({ __error: e.message }))
            : await apiCall("executeRemediation", apiPayload);

        if (response === null) {
            result.className = "result-box error";
            result.textContent =
                "Execution was not sent: the remediation API is not available in this page. No changes were made.";
            return;
        }

        if (response.__error) {
            result.className = "result-box error";
            result.textContent =
                `Execution failed: ${response.__error}`;
            return;
        }

        result.className = "result-box success";
        result.textContent =
            `Execution response:\n${JSON.stringify(response, null, 2)}`;
    }

    const executeRemediation = executeAction;

    /* --------------------------------------------------
       EVENT LISTENERS
    -------------------------------------------------- */

    function bindEvents() {
        $$(".nav-item").forEach(button => {
            button.addEventListener("click", () => {
                goToPage(button.dataset.page);
            });
        });

        $$("[data-go]").forEach(button => {
            button.addEventListener("click", () => {
                goToPage(button.dataset.go);
            });
        });

        $("#layoutToggle").addEventListener("click", () => {
            const shell = $("#appShell");

            const isTop = shell.classList.toggle("nav-top");

            $("#layoutToggleText").textContent = isTop
                ? "Move nav to side"
                : "Move nav to top";

            $("#layoutToggle").title = isTop
                ? "Move navigation to left sidebar"
                : "Move navigation to top";

            notify(
                isTop
                    ? "Navigation moved to the top."
                    : "Navigation moved to the sidebar."
            );
        });

        $("#openSidebar").addEventListener("click", () => {
            $("#sidebar").classList.add("mobile-open");
            $("#sidebarScrim").classList.add("visible");
        });

        $("#closeSidebar").addEventListener(
            "click",
            closeMobileNav
        );

        $("#sidebarScrim").addEventListener(
            "click",
            closeMobileNav
        );

        $("#refreshButton").addEventListener("click", async () => {
            await loadIncidents();
            notify("Incident data refreshed.");
        });

        $("#reloadIncidents").addEventListener("click", async () => {
            await loadIncidents();
            notify("Incident queue refreshed.");
        });

        $("#incidentSearch").addEventListener(
            "input",
            renderIncidents
        );

        $("#severityFilter").addEventListener(
            "change",
            renderIncidents
        );

        $("#timelineIncidentSelect").addEventListener(
            "change",
            async event => {
                await selectIncident(event.target.value);
            }
        );

        $("#incidentList").addEventListener(
            "click",
            async event => {
                const button = event.target.closest(
                    "[data-incident-id]"
                );

                if (!button) return;

                await selectIncident(button.dataset.incidentId);
            }
        );

        $("#overviewIncidentList").addEventListener(
            "click",
            async event => {
                const button = event.target.closest(
                    "[data-incident-id]"
                );

                if (!button) return;

                await selectIncident(button.dataset.incidentId);

                goToPage("incidents");
            }
        );

        $("#recommendationsContent").addEventListener(
            "click",
            event => {
                const button = event.target.closest(
                    "[data-recommendation]"
                );

                if (!button) return;

                const recommendations =
                    Array.isArray(state.recommendations)
                        ? state.recommendations
                        : demoRecommendations;

                const index =
                    Number(button.dataset.recommendation);

                const recommendation =
                    recommendations[index]
                    || demoRecommendations[0];

                const selectedAction =
                    button.dataset.action
                    || recommendation.action
                    || "restart_pod";

                const supportedActions = [
                    "restart_pod",
                    "scale_deployment",
                    "rollback_deployment",
                    "clear_cache"
                ];

                if (supportedActions.includes(selectedAction)) {
                    $("#remediationAction").value = selectedAction;
                } else {
                    notify(
                        "This recommendation is not a supported remediation action."
                    );
                    return;
                }

                const incident = state.incidents.find(
                    item =>
                        incidentId(item) === state.selectedIncident
                );

                $("#remediationTarget").value =
                    incident ? serviceOf(incident) : "";

                $$(".recommendation-card").forEach(card => {
                    card.classList.remove("chosen");
                });

                button.closest(
                    ".recommendation-card"
                )?.classList.add("chosen");

                goToPage("remediation");

                notify(
                    "Recommendation copied into the remediation console."
                );
            }
        );

        $("#logSearch").addEventListener(
            "input",
            renderLogs
        );

        $("#logLevelFilter").addEventListener(
            "change",
            renderLogs
        );

        $("#dryRunButton").addEventListener(
            "click",
            runDryRun
        );

        $("#remediationForm").addEventListener(
            "submit",
            executeAction
        );
    }

    /* --------------------------------------------------
       INITIALIZATION
    -------------------------------------------------- */

    function init() {
        $("#currentDate").textContent =
            new Intl.DateTimeFormat(undefined, {
                month: "short",
                day: "numeric",
                year: "numeric"
            }).format(new Date());

        $("#footerYear").textContent =
            `© ${new Date().getFullYear()}`;

        bindEvents();
        renderChart();
        renderLogs();

        loadIncidents().catch(error => {
            console.error("Failed to initialize incidents:", error);
            notify("Could not load incident data. Check the API connection.");
        });
    }

    /* Expose key handlers to window */
    window.selectIncident = selectIncident;
    window.getRemediationAction = getRemediationAction;
    window.runDryRun = runDryRun;
    window.executeAction = executeAction;

    document.addEventListener(
        "DOMContentLoaded",
        init
    );
})();