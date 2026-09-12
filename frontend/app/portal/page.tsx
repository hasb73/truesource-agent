"use client";

import { useEffect, useMemo, useState } from "react";

type PortalDoc = { id: string; application: string; title: string; version: number; author: string; last_modified: string; labels?: string[]; content: string };
type PortalPayload = { confluence: PortalDoc[]; sharepoint: PortalDoc[] };
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function initials(name: string) { return name.split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase(); }
function formatDate(value: string) { return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" }).format(new Date(value)); }
function sectionedContent(content: string) {
  const lines = content.split("\n").filter(Boolean);
  return { intro: lines[0] || "Architecture overview", facts: lines.slice(1).map((line) => { const [label, ...value] = line.split(":"); return { label, value: value.join(":").trim() }; }) };
}

export default function PortalPage() {
  const [payload, setPayload] = useState<PortalPayload>({ confluence: [], sharepoint: [] });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(false);
  const [confluenceDraft, setConfluenceDraft] = useState("");
  const [sharepointDraft, setSharepointDraft] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [starred, setStarred] = useState(false);

  async function refreshPortal() {
    const response = await fetch(`${API}/api/docs/portal`, { cache: "no-store" });
    const data = await response.json();
    setPayload(data);
    if (!selectedId && data.confluence.length > 0) setSelectedId(data.confluence[0].id);
  }

  useEffect(() => { void refreshPortal(); }, []);
  const filtered = useMemo(() => {
    const text = query.trim().toLowerCase();
    if (!text) return payload.confluence;
    return payload.confluence.filter((item) => [item.title, item.application, item.content, ...(item.labels || [])].join(" ").toLowerCase().includes(text));
  }, [payload, query]);
  const selected = filtered.find((item) => item.id === selectedId) || filtered[0] || null;
  const mirror = payload.sharepoint.find((item) => item.application === selected?.application) || null;
  const content = sectionedContent(selected?.content || "");

  useEffect(() => {
    setConfluenceDraft(selected?.content || ""); setSharepointDraft(mirror?.content || ""); setNotice(null); setEditing(false); setStarred(false);
  }, [selected?.id, mirror?.id]);

  async function saveConfluence(runScan = false) {
    if (!selected) return;
    setBusy(runScan ? "confluence+scan" : "confluence"); setNotice(null);
    const updateResponse = await fetch(`${API}/api/docs/portal/confluence/${selected.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: confluenceDraft, source: "confluence" }) });
    if (!updateResponse.ok) { setNotice("Could not publish this page. Check reviewer access and try again."); setBusy(null); return; }
    if (runScan) {
      await fetch(`${API}/api/scan`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scope: [selected.application], trigger: "portal_edit" }) });
      setNotice("Page published and a knowledge verification scan has been queued.");
    } else setNotice("Page published. The next scheduled scan will verify the change.");
    await refreshPortal(); setEditing(false); setBusy(null);
  }

  async function saveSharepoint() {
    if (!mirror) return;
    setBusy("sharepoint");
    const response = await fetch(`${API}/api/docs/portal/sharepoint/${mirror.id}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: sharepointDraft, source: "sharepoint" }) });
    setNotice(response.ok ? "Linked SharePoint reference updated." : "Could not update the linked SharePoint reference.");
    if (response.ok) await refreshPortal(); setBusy(null);
  }

  return <main className="confluence-shell">
    <header className="confluence-topbar">
      <a className="confluence-brand" href="/portal"><span className="confluence-mark">C</span><strong>TrueSource</strong></a>
      <nav className="confluence-global-nav" aria-label="Global navigation"><button className="active">Spaces</button><a href="/graph">Graph</a><button>People</button><button>Templates</button><button>Apps</button></nav>
      <div className="confluence-topbar-actions"><label className="confluence-search"><span>⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search knowledge" /></label><button className="confluence-create" onClick={() => setEditing(true)}>Create</button><button className="confluence-icon" title="Notifications">♢</button><div className="confluence-avatar">TS</div></div>
    </header>
    <div className="confluence-workspace">
      <aside className="confluence-sidebar">
        <div className="space-heading"><div className="space-icon">◈</div><div><strong>Engineering</strong><span>Knowledge space</span></div><button>•••</button></div><button className="space-overview">▦ Overview</button>
        <div className="sidebar-section-heading"><span>CONTENT</span><button>＋</button></div><div className="page-tree"><button className="tree-parent">⌄ Architecture</button>{filtered.map((item) => <button key={item.id} className={`tree-page ${selected?.id === item.id ? "selected" : ""}`} onClick={() => setSelectedId(item.id)}><span>▤</span>{item.title.replace(" Architecture", "")}</button>)}{filtered.length === 0 && <div className="tree-empty">No pages found</div>}</div><div className="sidebar-footer"><button>⌘ All content</button><button>♧ Space settings</button></div>
      </aside>
      <section className="confluence-main">
        {!selected ? <div className="empty">No knowledge page is available.</div> : <>
          <div className="breadcrumbs"><span>Engineering</span><b>/</b><span>Architecture</span><b>/</b><strong>{selected.application}</strong></div>
          <div className="page-toolbar"><div className="page-status"><span className="published-dot" /> Published</div><div className="page-toolbar-actions"><button onClick={() => setStarred(!starred)} className={starred ? "starred" : ""}>{starred ? "★ Saved" : "☆ Save"}</button><button>↗ Share</button><button onClick={() => setEditing(!editing)}>{editing ? "Cancel edit" : "✎ Edit"}</button><button className="more-button">•••</button></div></div>
          <article className="confluence-document">
            <div className="page-title-row"><h1>{selected.title}</h1><span className="page-id">{selected.id}</span></div><div className="author-row"><div className="author-avatar">{initials(selected.author)}</div><div><strong>{selected.author}</strong><span>updated {formatDate(selected.last_modified)} · {selected.version > 1 ? `v${selected.version}` : "first version"}</span></div></div><div className="document-rule" />
            <p className="document-lead">This page is the operational architecture reference for <b>{selected.application}</b>. It is monitored by TrueSource and compared with corroborating deployment evidence.</p>
            <section className="document-section"><h2>Overview</h2><p>{content.intro}</p></section><section className="document-section"><h2>Current architecture</h2><div className="architecture-table"><div className="table-head"><span>Capability</span><span>Current standard</span><span>Verification</span></div>{content.facts.map((fact) => <div className="table-row" key={fact.label}><span>{fact.label}</span><strong>{fact.value || "Not documented"}</strong><span className="verified-cell">● Source monitored</span></div>)}</div></section>
            <section className="info-panel"><span>✦</span><div><strong>Knowledge assurance</strong><p>Operational values are continuously checked against AWS, GitLab, Jira, and ServiceNow. A change to this page may trigger a review request.</p></div></section><section className="document-section"><h2>Related resources</h2><div className="resource-cards"><div><span>RUNBOOK</span><strong>{selected.application} production runbook</strong><small>Operational response procedures</small></div><div><span>SERVICE</span><strong>{selected.application} service catalog</strong><small>Ownership and escalation path</small></div></div></section><div className="page-labels">{(selected.labels || ["architecture", selected.application.toLowerCase()]).map((label) => <span key={label}>{label}</span>)}</div>
          </article>
          {editing && <section className="editor-panel"><div className="editor-panel-heading"><div><span>EDITING PAGE</span><h2>{selected.title}</h2><p>Publish changes to the knowledge source. Use verification scan when the update reflects a production change.</p></div><button className="confluence-icon" onClick={() => setEditing(false)}>×</button></div><textarea value={confluenceDraft} onChange={(event) => setConfluenceDraft(event.target.value)} aria-label="Edit Confluence page" /><div className="editor-actions"><button className="secondary" onClick={() => setEditing(false)} disabled={busy !== null}>Cancel</button><button className="secondary" onClick={() => void saveConfluence(false)} disabled={busy !== null}>{busy === "confluence" ? "Publishing…" : "Publish"}</button><button className="primary" onClick={() => void saveConfluence(true)} disabled={busy !== null}>{busy === "confluence+scan" ? "Publishing…" : "Publish + verify"}</button></div></section>}
          {notice && <div className="portal-notice">{notice}</div>}
        </>}
      </section>
      <aside className="confluence-context">{selected && <><div className="context-block"><h3>On this page</h3><a href="#">Overview</a><a href="#">Current architecture</a><a href="#">Related resources</a></div><div className="context-block"><h3>Page details</h3><dl><dt>Owner</dt><dd>{selected.author}</dd><dt>Last verified</dt><dd>{formatDate(selected.last_modified)}</dd><dt>Page status</dt><dd><span className="context-status">Published</span></dd><dt>Source</dt><dd>Confluence Cloud</dd></dl></div><div className="context-block linked-doc"><div className="linked-doc-heading"><h3>Linked reference</h3><span>SharePoint</span></div>{mirror ? <><strong>{mirror.title}</strong><small>{mirror.id} · v{mirror.version}</small><textarea value={sharepointDraft} onChange={(event) => setSharepointDraft(event.target.value)} aria-label="Edit linked SharePoint reference" /><button className="secondary" onClick={() => void saveSharepoint()} disabled={busy !== null}>{busy === "sharepoint" ? "Saving…" : "Update reference"}</button></> : <p>No linked reference found.</p>}</div></>}</aside>
    </div>
  </main>;
}
