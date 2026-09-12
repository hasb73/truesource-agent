"use client";

import { useEffect, useState } from "react";

import { AuthControls } from "../components/auth-controls";
import { CopilotAssistant } from "../components/copilot-assistant";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SERVICE_LINKS = [
  { label: "Backend API", href: "http://localhost:8000/docs" },
  { label: "AWS Mock", href: "http://localhost:8001/docs" },
  { label: "GitLab Mock", href: "http://localhost:8002/docs" },
  { label: "Jira Mock", href: "http://localhost:8003/docs" },
  { label: "ServiceNow Mock", href: "http://localhost:8004/docs" },
  { label: "Confluence Mock", href: "http://localhost:8005/docs" },
  { label: "SharePoint Mock", href: "http://localhost:8006/docs" },
];

type Evidence = {
  source: string;
  fact: string;
  supports: boolean;
};

type ProposedChange = {
  source: string;
  document: string;
  document_id: string;
  before: string;
  after: string;
};

type Drift = {
  id: string;
  title: string;
  application: string;
  attribute: string;
  severity: string;
  documented_value: string;
  observed_value: string;
  confidence: number;
  status: string;
  finding: string;
  rationale: string;
  confidence_breakdown: {
    explanation: string;
    supporting_sources: string[];
    contradicting_sources: string[];
  };
  affected_documents: string[];
  evidence: Evidence[];
  proposed_changes: ProposedChange[];
};

type ScanRun = {
  id: string;
  status: string;
  summary?: string | null;
  incident_ids: string[];
  activity: { time: string; status: string; message: string }[];
};

type Dashboard = {
  documents: number;
  health: number;
  open_drift: number;
  verified: number;
  stale: number;
  auto_fixed: number;
  knowledge: {
    facts: { attribute: string; value: string; confidence: number; status: string; verified_at: string; sources: string[] }[];
    documents_updated: string[];
  };
  latest_scan: ScanRun | null;
  runtime: RuntimeState["llm"];
  auth: RuntimeState["auth"];
};

type AuditEvent = {
  time: string;
  event: string;
};

type FirewallIncident = {
  id: string;
  time: string;
  source: string;
  source_reference: string;
  decision: string;
  risk: number;
  signals: string[];
  checks: string[];
  actions: string[];
  context_checks?: { label: string; result: string; status: "pass" | "warning" }[];
};

type DocumentRow = {
  id: string;
  source: string;
  title: string;
  version: number;
  status: string;
  application: string;
};

type RuntimeState = {
  auth: {
    mode: string;
    default_role?: string;
  };
  llm: {
    active_provider: string;
    providers: Record<string, { configured: boolean; model: string; base_url?: string }>;
  };
  copilotkit: {
    runtime_url?: string | null;
    agent_id: string;
  };
};

type Actor = {
  id: string;
  name: string;
  role: string;
  tenant_id: string;
};

type DemoScenario = {
  id: string;
  name: string;
  summary: string;
};

export default function Home() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [drifts, setDrifts] = useState<Drift[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [scanRun, setScanRun] = useState<ScanRun | null>(null);
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [runtime, setRuntime] = useState<RuntimeState | null>(null);
  const [actor, setActor] = useState<Actor | null>(null);
  const [provider, setProvider] = useState<string>("deterministic");
  const [question, setQuestion] = useState("How is Payments deployed?");
  const [answer, setAnswer] = useState<any>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [firewallIncidents, setFirewallIncidents] = useState<FirewallIncident[]>([]);
  const [attackArmed, setAttackArmed] = useState(false);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);

  const selected = drifts.find((item) => item.id === selectedId) || null;

  async function apiFetch(path: string, init?: RequestInit) {
    return fetch(`${API}${path}`, { ...init, cache: "no-store" });
  }

  async function refresh() {
    const [dashboardData, driftData, documentData, auditData, runtimeData, actorResponse, firewallData, scenarioData] = await Promise.all([
      apiFetch("/api/dashboard").then((response) => response.json()),
      apiFetch("/api/drift").then((response) => response.json()),
      apiFetch("/api/documents").then((response) => response.json()),
      apiFetch("/api/audit").then((response) => response.json()),
      apiFetch("/api/runtime").then((response) => response.json()),
      apiFetch("/api/auth/me").catch(() => null),
      apiFetch("/api/firewall/incidents").then((response) => response.json()),
      apiFetch("/api/demo/scenarios").then((response) => response.json()).catch(() => []),
    ]);
    setDashboard(dashboardData);
    setDrifts(driftData);
    setDocuments(documentData);
    setAudit([...auditData].reverse());
    setRuntime(runtimeData);
    setFirewallIncidents(firewallData);
    if (runtimeData?.llm?.active_provider) {
      setProvider((current) => current === "deterministic" ? runtimeData.llm.active_provider : current);
    }
    if (actorResponse && actorResponse.ok) {
      setActor(await actorResponse.json());
    } else {
      setActor({ id: "demo-reviewer", name: "Demo Reviewer", role: "administrator", tenant_id: "demo-airline" });
    }
    if (!selectedId && driftData.length) {
      setSelectedId(driftData[driftData.length - 1].id);
    }
    setScenarios(Array.isArray(scenarioData) ? scenarioData : []);
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function delay(ms: number) {
    await new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function changeReality() {
    await applyScenario("eks_migration");
  }

  async function applyScenario(scenario: string) {
    setBusyAction(`scenario:${scenario}`);
    try {
      await apiFetch("/api/demo/change", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario }),
      });
      await refresh();
    } finally {
      setBusyAction(null);
    }
  }

  async function resetDemo() {
    setBusyAction("reset");
    await apiFetch("/api/demo/reset", { method: "POST" });
    setAnswer(null);
    setScanRun(null);
    setSelectedId(null);
    setAttackArmed(false);
    await refresh();
    setBusyAction(null);
  }

  async function injectAgentAttack() {
    setBusyAction("attack");
    const response = await apiFetch("/api/demo/inject-agent-attack", { method: "POST" });
    if (response.ok) setAttackArmed(true);
    await refresh();
    setBusyAction(null);
  }

  async function queueAndWaitForScan(trigger: string) {
    const response = await apiFetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scope: ["Payments"], trigger, provider }),
    });
    if (!response.ok) {
      return;
    }
    const created = await response.json();
    for (let attempt = 0; attempt < 20; attempt += 1) {
      const status = await apiFetch(`/api/scans/${created.scan_id}`).then((result) => result.json());
      setScanRun(status);
      if (status.status === "completed") {
        break;
      }
      await delay(350);
    }
  }

  async function runScan() {
    setBusyAction("scan");
    try {
      await queueAndWaitForScan("manual");
      await refresh();
    } finally {
      setBusyAction(null);
    }
  }

  async function approve() {
    if (!selected) {
      return;
    }
    setBusyAction("approve");
    await apiFetch(`/api/drift/${selected.id}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason: "Operational evidence is conclusive." }),
    });
    await refresh();
    setBusyAction(null);
  }

  async function ask() {
    setBusyAction("ask");
    const response = await apiFetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, provider }),
    });
    setAnswer(await response.json());
    setBusyAction(null);
  }

  const runtimeLabel = runtime?.llm.active_provider ?? dashboard?.runtime?.active_provider ?? "deterministic";
  const authMode = runtime?.auth.mode ?? dashboard?.auth?.mode ?? "development";
  const copilotConfigured = Boolean(runtime?.copilotkit.runtime_url);
  const reviewDisabled = !actor;

  return (
    <main>
      <header className="topbar">
        <div>
          <div className="brand">TrueSource</div>
          <div className="tagline">Self-healing enterprise knowledge layer</div>
        </div>
        <div className="topbar-actions">
          <div className="pill firewall-pill">AgentFirewall · enforcing</div>
          <div className="pill">● Knowledge health {dashboard?.health ?? "--"}%</div>
          <a className="secondary doc-link" href="/portal">Open Docs Portal</a>
          <a className="secondary doc-link" href="/graph">Knowledge Graph</a>
          <AuthControls actor={actor} />
        </div>
      </header>

      <section className="service-links">
        <div className="service-links-title">Child Services</div>
        <div className="service-links-list">
          {SERVICE_LINKS.map((service) => (
            <a key={service.label} className="service-link-chip" href={service.href} target="_blank" rel="noreferrer">
              {service.label}
            </a>
          ))}
        </div>
      </section>

      <section className="hero">
        <div>
          <p className="eyebrow">ENTERPRISE TRUTH INFRASTRUCTURE</p>
          <h1>Keep AI grounded in what the company actually does.</h1>
          <p className="lead">
            Detect documentation drift, verify it against operational evidence,
            repair the knowledge layer, and feed only verified truth to downstream agents.
          </p>
          <div className="hero-meta">
            <div className="hero-chip">Auth: {authMode}</div>
            <div className="hero-chip">LLM: {runtimeLabel}</div>
            <div className="hero-chip">CopilotKit: {copilotConfigured ? "connected" : "standby"}</div>
          </div>
        </div>
        <div className="hero-actions">
          <select className="provider-select" aria-label="Model provider" value={provider} onChange={(event) => setProvider(event.target.value)}>
            {runtime && Object.entries(runtime.llm.providers).map(([key, value]) => (
              <option key={key} value={key} disabled={!value.configured && key !== "deterministic"}>
                {key} · {value.model}
              </option>
            ))}
            {!runtime && <option value="deterministic">deterministic</option>}
          </select>
          <button className="secondary" onClick={resetDemo} disabled={busyAction !== null}>
            {busyAction === "reset" ? "Resetting…" : "Reset Demo"}
          </button>
          <button className="secondary" onClick={changeReality} disabled={busyAction !== null || reviewDisabled}>
            {busyAction === "scenario:eks_migration" ? "Simulating…" : "Simulate Migration → EKS"}
          </button>
          <button className="secondary" onClick={() => void applyScenario("database_modernization")} disabled={busyAction !== null || reviewDisabled}>
            {busyAction === "scenario:database_modernization" ? "Simulating…" : "Simulate DB Modernization"}
          </button>
          <button className="secondary" onClick={() => void applyScenario("region_failover")} disabled={busyAction !== null || reviewDisabled}>
            {busyAction === "scenario:region_failover" ? "Simulating…" : "Simulate Region Failover"}
          </button>
          <button className="secondary" onClick={() => void applyScenario("gitops_rollout")} disabled={busyAction !== null || reviewDisabled}>
            {busyAction === "scenario:gitops_rollout" ? "Simulating…" : "Simulate GitOps Rollout"}
          </button>
            <button className="danger-button" aria-describedby="attack-description" onClick={injectAgentAttack} disabled={busyAction !== null || attackArmed}>
              {busyAction === "attack" ? "Simulating…" : attackArmed ? "Malicious edit ready" : "Simulate malicious Confluence edit"}
            </button>
          <button className="primary" onClick={runScan} disabled={busyAction !== null || reviewDisabled}>
            {busyAction === "scan" ? "Scanning…" : "Run Scan"}
          </button>
          <p className="attack-description" id="attack-description">The malicious edit adds a hidden instruction asking TrueSource to ignore AWS and GitLab evidence.</p>
        </div>
      </section>

      {scenarios.length > 0 && (
        <section className="card scenario-strip">
          <div className="card-title">Available change scenarios</div>
          <div className="mini-stack">
            {scenarios.map((item) => (
              <div className="mini notice" key={item.id}>
                <b>{item.name}</b>
                <span>{item.summary}</span>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="stats">
        <Stat label="Documentation health" value={`${dashboard?.health ?? "—"}%`} />
        <Stat label="Documents monitored" value={dashboard?.documents ?? "—"} />
        <Stat label="Open incidents" value={dashboard?.open_drift ?? "—"} />
        <Stat label="Verified facts" value={dashboard?.verified ?? "—"} />
        <Stat label="Agent attacks blocked" value={firewallIncidents.length} />
      </section>

      <KnowledgeGraphOverview documents={documents} drifts={drifts} />

      <section className={`firewall-console ${firewallIncidents.length ? "has-incident" : ""}`}>
        <div className="firewall-heading">
          <div>
            <span className="firewall-eyebrow">AGENTIC SECURITY SUPERVISOR</span>
            <h2>AgentFirewall</h2>
            <p>Inspects untrusted evidence before model access and validates document writes before execution.</p>
          </div>
          <div className="firewall-state">{firewallIncidents.length ? "THREAT CONTAINED" : attackArmed ? "EDIT PENDING SCAN" : "MONITORING"}</div>
        </div>
        {firewallIncidents.length === 0 ? (
          <div className="firewall-idle">
            <div><b>Ingress guard</b><span>Confluence, SharePoint, Jira, GitLab</span></div>
            <div><b>Action guard</b><span>Reviewer identity, diff scope, write target</span></div>
            <div><b>Decision</b><span>Allow · Review · Block</span></div>
          </div>
        ) : (
          <div className="firewall-incident">
            <div className="firewall-summary">
              <small>Confluence · CONF-121 · High risk {firewallIncidents[0].risk}/100</small>
              <h3>Malicious Confluence edit blocked</h3>
              <p>A hidden instruction tried to control the agent’s conclusion and bypass trusted evidence.</p>
            </div>
            <div className="context-checks">
              {firewallIncidents[0].context_checks?.map((check) => (
                <div className={`context-check ${check.status}`} key={check.label}>
                  <span>{check.label}</span>
                  <strong>{check.result}</strong>
                </div>
              ))}
            </div>
            <div className="firewall-outcome">
              <b>Blocked safely</b>
              <span>Instruction removed. AI tools denied. Scan continued using trusted evidence.</span>
            </div>
            <details className="firewall-details">
              <summary>Show technical details</summary>
              <div className="signal-list">
                {firewallIncidents[0].signals.map((signal) => <span key={signal}>{signal}</span>)}
              </div>
              <ol className="firewall-trace">
                {firewallIncidents[0].checks.concat(firewallIncidents[0].actions).map((step, index) => (
                  <li key={`${step}-${index}`}><span>{String(index + 1).padStart(2, "0")}</span>{step}</li>
                ))}
              </ol>
            </details>
          </div>
        )}
      </section>

      <section className="grid">
        <div className="card">
          <div className="card-title">Knowledge incidents</div>
          {drifts.length === 0 && <div className="empty">No drift detected.</div>}
          {drifts.map((drift) => (
            <button
              key={drift.id}
              className={`drift ${selected?.id === drift.id ? "selected" : ""}`}
              onClick={() => setSelectedId(drift.id)}
            >
              <div className="severity">{drift.severity}</div>
              <div className="drift-main">
                <strong>{drift.title}</strong>
                <span>{drift.documented_value} → {drift.observed_value}</span>
              </div>
              <div className="confidence">{Math.round(drift.confidence * 100)}%</div>
            </button>
          ))}
        </div>

        <div className="card">
          <div className="card-title">Evidence explorer</div>
          {!selected && <div className="empty">Simulate the migration and run a scan to create a knowledge incident.</div>}
          {selected && (
            <>
              <div className="finding">
                <span className="warning">KNOWLEDGE DRIFT DETECTED</span>
                <h2>{selected.documented_value} → {selected.observed_value}</h2>
                <p>Confidence: <b>{Math.round(selected.confidence * 100)}%</b></p>
                <p>{selected.finding}</p>
                <p className="subtle">{selected.rationale}</p>
              </div>
              <div className="evidence-list">
                {selected.evidence.map((item, index) => (
                  <div className="evidence" key={`${item.source}-${index}`}>
                    <div className={`dot ${item.supports ? "yes" : "no"}`}></div>
                    <div>
                      <b>{item.source}</b>
                      <span>{item.fact}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="support-list">
                <div><b>Supporting:</b> {selected.confidence_breakdown.supporting_sources.join(", ")}</div>
                <div><b>Contradicting:</b> {selected.confidence_breakdown.contradicting_sources.join(", ")}</div>
              </div>
              <div className="diff">
                <div className="diff-title">Proposed documentation repair</div>
                {selected.proposed_changes.map((change, index) => (
                  <div key={`${change.document}-${index}`} className="change">
                    <small>{change.document}</small>
                    <div className="minus">− {change.before}</div>
                    <div className="plus">+ {change.after}</div>
                  </div>
                ))}
              </div>
              {selected.status === "pending_review" && (
                <div className="actions">
                  <button className="primary" onClick={approve} disabled={busyAction !== null || reviewDisabled}>Approve & refresh verified RAG</button>
                  <button className="secondary" onClick={() => void refresh()} disabled={busyAction !== null}>Review later</button>
                </div>
              )}
              {selected.status === "resolved" && <div className="success">✓ Documentation repaired and knowledge verified.</div>}
            </>
          )}
        </div>
      </section>

      <section className="grid lower-grid">
        <div className="card">
          <div className="card-title">Agent activity</div>
          {!scanRun && <div className="empty">Run a scan to watch the agent workflow.</div>}
          {scanRun && (
            <div className="timeline">
              {scanRun.activity.map((item, index) => (
                <div className="timeline-item" key={`${item.time}-${index}`}>
                  <span className={`timeline-dot ${item.status}`}></span>
                  <div>
                    <b>{item.message}</b>
                    <span>{new Date(item.time).toLocaleTimeString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">Documents in scope</div>
          <div className="doc-list">
            {documents.map((document) => (
              <div className="doc-row" key={document.id}>
                <div>
                  <b>{document.title}</b>
                  <span>{document.source} · v{document.version}</span>
                </div>
                <div className={`doc-status ${document.status.toLowerCase()}`}>{document.status}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="card ask">
        <div className="card-title">Verified RAG / Ask the company</div>
        <div className="ask-row">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} />
          <button className="primary" onClick={ask} disabled={busyAction !== null}>
            {busyAction === "ask" ? "Asking…" : "Ask"}
          </button>
        </div>
        {answer && (
          <div className="answer">
            <p>{answer.answer}</p>
            <div className="trust-card">
              <div><span>Confidence</span><strong>{Math.round((answer.trust_card.confidence || 0) * 100)}%</strong></div>
              <div><span>Verified</span><strong>{answer.trust_card.verified_at ? new Date(answer.trust_card.verified_at).toLocaleString() : "Unknown"}</strong></div>
              <div><span>Sources</span><strong>{(answer.trust_card.sources || []).join(", ") || "None"}</strong></div>
              <div><span>Docs updated</span><strong>{(answer.trust_card.documents_updated || []).join(", ") || "Not yet"}</strong></div>
              <div><span>Provider</span><strong>{answer.trust_card.provider || provider}</strong></div>
            </div>
          </div>
        )}
      </section>

      <section className="grid lower-grid">
        <div className="card">
          <div className="card-title">Audit trail</div>
          <div className="timeline">
            {audit.slice(0, 8).map((item, index) => (
              <div className="timeline-item" key={`${item.time}-${index}`}>
                <span className="timeline-dot ok"></span>
                <div>
                  <b>{item.event.replaceAll("_", " ")}</b>
                  <span>{new Date(item.time).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Embedded agent surfaces</div>
          <div className="mini-stack">
            <div className="mini notice"><b>Teams / Slack</b><span>Mock notification when drift is detected and ready for review.</span></div>
            <div className="mini notice"><b>Confluence</b><span>Reviewer opens evidence and approves the proposed documentation repair.</span></div>
            <div className="mini notice"><b>RAG / AI agents</b><span>Only verified facts are exposed through the trust card and answer flow.</span></div>
            <div className="mini notice"><b>Development auth + CopilotKit</b><span>Local reviewer workflow is active. {copilotConfigured ? "Copilot sidebar is available." : "Copilot runtime can be enabled with an environment variable."}</span></div>
          </div>
        </div>
      </section>

      <CopilotAssistant runtimeUrl={runtime?.copilotkit.runtime_url || null} agentId={runtime?.copilotkit.agent_id || "truesource_guardian"} />

      <section className="footer-grid">
        <div className="mini">
          <b>OpenAI</b><span>Reasoning + enterprise answer generation</span>
        </div>
        <div className="mini">
          <b>CopilotKit</b><span>Agentic UI / human-in-the-loop surface</span>
        </div>
        <div className="mini">
          <b>Trigger.dev</b><span>Continuous drift scans and workflows</span>
        </div>
        <div className="mini">
          <b>PostgreSQL</b><span>Persistent control-plane and audit state</span>
        </div>
      </section>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong></div>;
}

function KnowledgeGraphOverview({ documents, drifts }: { documents: DocumentRow[]; drifts: Drift[] }) {
  const applications = Array.from(new Set(documents.map((document) => document.application))).filter(Boolean).slice(0, 5);
  const activeDriftApps = new Set(drifts.filter((drift) => !["resolved", "rejected"].includes(drift.status)).map((drift) => drift.application));
  const operationalSystems = ["AWS", "GitLab", "Jira", "ServiceNow"];
  const documentationSystems = ["Confluence", "SharePoint"];

  return (
    <section className="homepage-graph">
      <div className="homepage-graph-head">
        <div><span>KNOWLEDGE OBSERVABILITY</span><h2>Enterprise knowledge graph</h2><p>Operational systems verify documentation before facts reach enterprise AI.</p></div>
        <a className="secondary doc-link" href="/graph">Open detailed graph →</a>
      </div>
      <div className="homepage-graph-canvas">
        <svg viewBox="0 0 1140 420" role="img" aria-label="Enterprise knowledge graph showing source systems, TrueSource, applications, and documentation systems">
          <defs><marker id="homepage-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" /></marker></defs>
          {operationalSystems.map((_, index) => <line key={`source-${index}`} className="homepage-graph-edge source" x1="185" y1={78 + index * 78} x2="470" y2="185" markerEnd="url(#homepage-arrow)" />)}
          {documentationSystems.map((_, index) => <line key={`docs-${index}`} className="homepage-graph-edge docs" x1="955" y1={118 + index * 150} x2="670" y2="210" markerEnd="url(#homepage-arrow)" />)}
          {applications.map((_, index) => <line key={`app-${index}`} className="homepage-graph-edge app" x1="570" y1="260" x2={175 + index * 195} y2="342" markerEnd="url(#homepage-arrow)" />)}
          {operationalSystems.map((name, index) => <g className="homepage-graph-node source-node" key={name} transform={`translate(35, ${52 + index * 78})`}><rect width="150" height="50" rx="7" /><text x="14" y="23">{name}</text><text className="node-subtitle" x="14" y="39">operational evidence</text></g>)}
          {documentationSystems.map((name, index) => <g className="homepage-graph-node docs-node" key={name} transform={`translate(955, ${93 + index * 150})`}><rect width="150" height="50" rx="7" /><text x="14" y="23">{name}</text><text className="node-subtitle" x="14" y="39">documentation source</text></g>)}
          <g className="homepage-graph-node guardian-node" transform="translate(470, 145)"><rect width="200" height="115" rx="10" /><text className="node-kicker" x="18" y="29">CONTROL PLANE</text><text x="18" y="59">TrueSource</text><text className="node-subtitle" x="18" y="81">verify · govern · repair</text><text className="node-subtitle" x="18" y="98">trusted knowledge only</text></g>
          {applications.map((application, index) => {
            const appDocuments = documents.filter((document) => document.application === application);
            const stale = appDocuments.some((document) => document.status === "STALE" || document.status === "QUARANTINED") || activeDriftApps.has(application);
            return <g className={`homepage-graph-node app-node ${stale ? "attention" : ""}`} key={application} transform={`translate(${100 + index * 195}, 342)`}><rect width="150" height="51" rx="7" /><text x="13" y="22">{application}</text><text className="node-subtitle" x="13" y="39">{stale ? "● needs review" : "● documentation verified"}</text></g>;
          })}
        </svg>
      </div>
      <div className="homepage-graph-legend"><span><i className="source" /> Operational evidence</span><span><i className="docs" /> Documentation sources</span><span><i className="app" /> Application knowledge</span><span><i className="alert" /> Needs review</span></div>
    </section>
  );
}
