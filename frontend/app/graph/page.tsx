"use client";

import { useEffect, useMemo, useState } from "react";

type DocumentRow = { id: string; source: string; title: string; version: number; status: string; application: string };
type PortalDoc = { id: string; application: string; title: string; version: number; author: string; last_modified: string; content: string };
type Drift = { id: string; application: string; title: string; status: string; confidence: number; documented_value: string; observed_value: string };
type Knowledge = { facts: { attribute: string; value: string; status: string; confidence: number; sources: string[]; verified_at: string }[] };

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const systems = [
  { id: "aws", label: "AWS", detail: "Runtime infrastructure", type: "operational", x: 90, y: 122 },
  { id: "gitlab", label: "GitLab", detail: "Deployments & code", type: "operational", x: 90, y: 250 },
  { id: "jira", label: "Jira", detail: "Delivery workflow", type: "operational", x: 90, y: 378 },
  { id: "servicenow", label: "ServiceNow", detail: "Change management", type: "operational", x: 90, y: 506 },
  { id: "confluence", label: "Confluence", detail: "Architecture knowledge", type: "documentation", x: 1110, y: 196 },
  { id: "sharepoint", label: "SharePoint", detail: "Reference documents", type: "documentation", x: 1110, y: 440 },
];

function statusClass(status: string) { return status.toLowerCase().replace(/[^a-z]/g, "-"); }

export default function KnowledgeGraphPage() {
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [pages, setPages] = useState<PortalDoc[]>([]);
  const [drifts, setDrifts] = useState<Drift[]>([]);
  const [knowledge, setKnowledge] = useState<Knowledge>({ facts: [] });
  const [selectedApp, setSelectedApp] = useState("Payments");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      const [documentResponse, portalResponse, driftResponse, knowledgeResponse] = await Promise.all([
        fetch(`${API}/api/documents`, { cache: "no-store" }), fetch(`${API}/api/docs/portal`, { cache: "no-store" }), fetch(`${API}/api/drift`, { cache: "no-store" }), fetch(`${API}/api/knowledge`, { cache: "no-store" }),
      ]);
      const [documentData, portalData, driftData, knowledgeData] = await Promise.all([documentResponse.json(), portalResponse.json(), driftResponse.json(), knowledgeResponse.json()]);
      setDocuments(Array.isArray(documentData) ? documentData : []);
      setPages(Array.isArray(portalData.confluence) ? portalData.confluence : []);
      setDrifts(Array.isArray(driftData) ? driftData : []);
      setKnowledge(knowledgeData || { facts: [] });
      if (portalData.confluence?.length && !portalData.confluence.some((item: PortalDoc) => item.application === "Payments")) setSelectedApp(portalData.confluence[0].application);
      setLoading(false);
    }
    void load();
  }, []);

  const applications = useMemo(() => pages.map((page) => page.application), [pages]);
  const focusedDocuments = documents.filter((document) => document.application === selectedApp);
  const focusedDrifts = drifts.filter((drift) => drift.application === selectedApp && !["resolved", "rejected"].includes(drift.status));
  const freshCount = documents.filter((document) => document.status === "VERIFIED").length;
  const staleCount = documents.filter((document) => document.status === "STALE").length;
  const focusedPage = pages.find((page) => page.application === selectedApp);
  const appPositions = useMemo(() => applications.map((application, index) => ({ application, x: 700, y: 94 + index * 122 })), [applications]);
  const focusedPosition = appPositions.find((item) => item.application === selectedApp) || { x: 700, y: 94 };

  return <main className="graph-shell">
    <header className="graph-topbar"><a href="/portal" className="graph-brand"><span>TS</span><strong>TrueSource</strong></a><div className="graph-crumb">Engineering knowledge <b>/</b> Dependency graph</div><div className="graph-top-actions"><a href="/portal">Docs portal</a><a href="/">Control plane</a></div></header>
    <section className="graph-heading"><div><p>KNOWLEDGE OBSERVABILITY</p><h1>Enterprise knowledge graph</h1><span>Trace operational evidence, governed documentation, and the systems that depend on them.</span></div><label>Focus application<select value={selectedApp} onChange={(event) => setSelectedApp(event.target.value)}>{applications.map((application) => <option value={application} key={application}>{application}</option>)}</select></label></section>
    <section className="graph-kpis"><div><span>Applications</span><strong>{applications.length || "—"}</strong></div><div><span>Documents monitored</span><strong>{documents.length || "—"}</strong></div><div><span>Verified documentation</span><strong>{freshCount}</strong></div><div className={staleCount ? "attention" : ""}><span>Stale documentation</span><strong>{staleCount}</strong></div></section>
    <section className="graph-layout">
      <div className="graph-canvas-wrap">
        <div className="graph-canvas-heading"><div><strong>System relationships</strong><span>Lines show evidence flow and documentation ownership.</span></div><div className="graph-legend"><span><i className="operational" /> Operational evidence</span><span><i className="documentation" /> Documentation</span><span><i className="application" /> Application</span></div></div>
        <div className="graph-canvas" aria-busy={loading}>
          {loading ? <div className="graph-loading">Loading the knowledge graph…</div> : <svg viewBox="0 0 1200 710" role="img" aria-label={`Knowledge graph focused on ${selectedApp}`}>
            <defs><marker id="graph-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" /></marker></defs>
            {systems.slice(0, 4).map((system) => <line className="graph-edge operational-edge" key={`${system.id}-truth`} x1={system.x + 135} y1={system.y + 34} x2="490" y2="341" markerEnd="url(#graph-arrow)" />)}
            {systems.slice(4).map((system) => <line className="graph-edge documentation-edge" key={`${system.id}-app`} x1={system.x - 130} y1={system.y + 34} x2={focusedPosition.x + 120} y2={focusedPosition.y + 35} markerEnd="url(#graph-arrow)" />)}
            {appPositions.map((app) => <line className={`graph-edge app-edge ${app.application === selectedApp ? "focused" : ""}`} key={`truth-${app.application}`} x1="655" y1="365" x2={app.x - 18} y2={app.y + 35} markerEnd="url(#graph-arrow)" />)}
            <line className="graph-edge trust-edge" x1="570" y1="420" x2="570" y2="587" markerEnd="url(#graph-arrow)" />
            {systems.map((system) => <g key={system.id} className={`graph-node system-node ${system.type}`} transform={`translate(${system.x - 92}, ${system.y})`}><rect width="184" height="68" rx="7" /><text className="node-title" x="16" y="28">{system.label}</text><text className="node-detail" x="16" y="49">{system.detail}</text></g>)}
            <g className="graph-node truth-node" transform="translate(475, 300)"><rect width="180" height="120" rx="10" /><text className="node-kicker" x="18" y="28">CONTROL PLANE</text><text className="node-title" x="18" y="55">TrueSource</text><text className="node-detail" x="18" y="79">Verifies & governs</text><text className="node-detail" x="18" y="98">knowledge changes</text></g>
            {appPositions.map((app) => <g key={app.application} className={`graph-node application-node ${app.application === selectedApp ? "selected" : ""}`} transform={`translate(${app.x}, ${app.y})`}><rect width="170" height="70" rx="7" /><text className="node-title" x="16" y="29">{app.application}</text><text className="node-detail" x="16" y="50">Application record</text></g>)}
            <g className="graph-node trust-node" transform="translate(457, 590)"><rect width="226" height="72" rx="8" /><text className="node-kicker" x="16" y="25">TRUSTED OUTPUT</text><text className="node-title" x="16" y="51">Verified knowledge layer</text></g>
          </svg>}
        </div>
      </div>
      <aside className="graph-inspector">
        <div className="inspector-header"><span>FOCUSED NODE</span><h2>{selectedApp}</h2><p>{focusedPage ? `Architecture page · ${focusedPage.id} · v${focusedPage.version}` : "Application record"}</p></div>
        <div className="inspector-section"><h3>Documentation status</h3>{focusedDocuments.length ? focusedDocuments.map((document) => <div className="document-status-row" key={document.id}><div><strong>{document.title}</strong><span>{document.source} · v{document.version}</span></div><b className={`graph-status ${statusClass(document.status)}`}>{document.status}</b></div>) : <p className="inspector-empty">No documents are connected to this application.</p>}</div>
        <div className="inspector-section"><h3>Evidence dependencies</h3><ul className="dependency-list"><li><span>AWS</span><small>runtime source</small></li><li><span>GitLab</span><small>deployment source</small></li><li><span>Jira</span><small>workflow source</small></li><li><span>ServiceNow</span><small>change source</small></li></ul></div>
        <div className="inspector-section"><h3>Knowledge state</h3>{knowledge.facts.map((fact) => <div className="fact-row" key={fact.attribute}><span>{fact.attribute}</span><strong>{fact.value}</strong><small>{Math.round(fact.confidence * 100)}% confidence</small></div>)}</div>
        {focusedDrifts.length > 0 && <div className="graph-alert"><strong>{focusedDrifts.length} open knowledge incident{focusedDrifts.length > 1 ? "s" : ""}</strong><span>{focusedDrifts[0].documented_value} → {focusedDrifts[0].observed_value} · {Math.round(focusedDrifts[0].confidence * 100)}% confidence</span><a href="/">Review in control plane →</a></div>}
      </aside>
    </section>
  </main>;
}
