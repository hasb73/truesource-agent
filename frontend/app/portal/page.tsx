"use client";

import { useEffect, useMemo, useState } from "react";

type PortalDoc = {
  id: string;
  application: string;
  title: string;
  version: number;
  author: string;
  last_modified: string;
  labels?: string[];
  content: string;
};

type PortalPayload = {
  confluence: PortalDoc[];
  sharepoint: PortalDoc[];
};

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PortalPage() {
  const [payload, setPayload] = useState<PortalPayload>({ confluence: [], sharepoint: [] });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [confluenceDraft, setConfluenceDraft] = useState("");
  const [sharepointDraft, setSharepointDraft] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function refreshPortal() {
    const response = await fetch(`${API}/api/docs/portal`, { cache: "no-store" });
    const data = await response.json();
    setPayload(data);
    if (!selectedId && data.confluence.length > 0) {
      setSelectedId(data.confluence[0].id);
    }
  }

  useEffect(() => {
    void refreshPortal();
  }, []);

  const filtered = useMemo(() => {
    const text = query.trim().toLowerCase();
    if (!text) {
      return payload.confluence;
    }
    return payload.confluence.filter((item) => {
      return (
        item.title.toLowerCase().includes(text) ||
        item.application.toLowerCase().includes(text) ||
        item.content.toLowerCase().includes(text)
      );
    });
  }, [payload, query]);

  const selected = filtered.find((item) => item.id === selectedId) || filtered[0] || null;
  const mirror = payload.sharepoint.find((item) => item.application === selected?.application) || null;

  useEffect(() => {
    setConfluenceDraft(selected?.content || "");
    setSharepointDraft(mirror?.content || "");
    setNotice(null);
  }, [selected?.id, mirror?.id]);

  async function saveConfluence(runScan = false) {
    if (!selected) {
      return;
    }
    setBusy(runScan ? "confluence+scan" : "confluence");
    setNotice(null);
    const updateResponse = await fetch(`${API}/api/docs/portal/confluence/${selected.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: confluenceDraft, source: "confluence" }),
    });
    if (!updateResponse.ok) {
      setBusy(null);
      setNotice("Failed to save Confluence draft.");
      return;
    }
    if (runScan) {
      await fetch(`${API}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scope: [selected.application], trigger: "portal_edit" }),
      });
      setNotice("Confluence saved and scan queued.");
    } else {
      setNotice("Confluence draft saved.");
    }
    await refreshPortal();
    setBusy(null);
  }

  async function saveSharepoint() {
    if (!mirror) {
      return;
    }
    setBusy("sharepoint");
    setNotice(null);
    const response = await fetch(`${API}/api/docs/portal/sharepoint/${mirror.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: sharepointDraft, source: "sharepoint" }),
    });
    if (!response.ok) {
      setBusy(null);
      setNotice("Failed to save SharePoint draft.");
      return;
    }
    await refreshPortal();
    setBusy(null);
    setNotice("SharePoint draft saved.");
  }

  return (
    <main className="portal-shell">
      <header className="portal-header">
        <div>
          <p className="portal-eyebrow">Knowledge Workspace</p>
          <h1>Confluence Portal Mock</h1>
          <p className="portal-subtitle">Browse architecture pages, compare with SharePoint mirrors, and inspect versioned content.</p>
        </div>
        <a className="secondary doc-link" href="/">Back To Control Plane</a>
      </header>

      <section className="portal-layout">
        <aside className="portal-sidebar">
          <div className="portal-search-wrap">
            <input
              className="portal-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search pages"
            />
          </div>
          <div className="portal-nav">
            {filtered.map((item) => (
              <button
                key={item.id}
                className={`portal-nav-item ${selected?.id === item.id ? "active" : ""}`}
                onClick={() => setSelectedId(item.id)}
              >
                <strong>{item.title}</strong>
                <span>{item.application} · v{item.version}</span>
              </button>
            ))}
            {filtered.length === 0 && <div className="empty">No pages match your search.</div>}
          </div>
        </aside>

        <article className="portal-content">
          {!selected && <div className="empty">Select a page to view documentation content.</div>}
          {selected && (
            <>
              <div className="portal-meta">
                <h2>{selected.title}</h2>
                <div className="portal-badges">
                  <span>Page ID: {selected.id}</span>
                  <span>Version: {selected.version}</span>
                  <span>Author: {selected.author}</span>
                  <span>Updated: {new Date(selected.last_modified).toLocaleString()}</span>
                </div>
                <div className="portal-labels">
                  {(selected.labels || []).map((label) => <span key={label}>{label}</span>)}
                </div>
              </div>

              <pre className="portal-doc">{selected.content}</pre>

              <div className="portal-editor-grid">
                <div className="portal-editor-card">
                  <div className="portal-editor-head">
                    <h3>Edit Confluence Page</h3>
                    <div className="portal-editor-actions">
                      <button className="secondary" onClick={() => void saveConfluence(false)} disabled={busy !== null}>
                        {busy === "confluence" ? "Saving..." : "Save"}
                      </button>
                      <button className="primary" onClick={() => void saveConfluence(true)} disabled={busy !== null}>
                        {busy === "confluence+scan" ? "Saving..." : "Save + Run Scan"}
                      </button>
                    </div>
                  </div>
                  <textarea
                    className="portal-editor"
                    value={confluenceDraft}
                    onChange={(event) => setConfluenceDraft(event.target.value)}
                  />
                </div>

                <div className="portal-editor-card">
                  <div className="portal-editor-head">
                    <h3>Edit SharePoint Mirror</h3>
                    <div className="portal-editor-actions">
                      <button className="secondary" onClick={() => void saveSharepoint()} disabled={busy !== null || !mirror}>
                        {busy === "sharepoint" ? "Saving..." : "Save Mirror"}
                      </button>
                    </div>
                  </div>
                  <textarea
                    className="portal-editor"
                    value={sharepointDraft}
                    onChange={(event) => setSharepointDraft(event.target.value)}
                    disabled={!mirror}
                  />
                </div>
              </div>

              {notice && <div className="portal-notice">{notice}</div>}

              <div className="portal-mirror">
                <h3>SharePoint mirror</h3>
                {payload.sharepoint
                  .filter((item) => item.application === selected.application)
                  .map((item) => (
                    <div key={item.id} className="portal-mirror-item">
                      <b>{item.title}</b>
                      <span>{item.id} · v{item.version}</span>
                      <pre>{item.content}</pre>
                    </div>
                  ))}
              </div>
            </>
          )}
        </article>
      </section>
    </main>
  );
}
