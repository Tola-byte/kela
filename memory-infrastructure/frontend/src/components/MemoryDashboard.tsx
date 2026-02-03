"use client";

import { useEffect, useState } from "react";
import { useMemoryContext } from "../hooks/useMemoryContext";
import MemoryTimeline from "./MemoryTimeline";
import ContextPreview from "./ContextPreview";

const DEFAULT_USER = "demo-user";

export default function MemoryDashboard() {
  const [userId, setUserId] = useState(DEFAULT_USER);
  const [query, setQuery] = useState("What do I know about growth?");
  const [ingestTitle, setIngestTitle] = useState("");
  const [ingestContent, setIngestContent] = useState("");
  const [ingestType, setIngestType] = useState("document");
  const [ingestTags, setIngestTags] = useState("");
  const [ingestSource, setIngestSource] = useState("");
  const {
    stats,
    entries,
    context,
    ingestResult,
    fetchStats,
    fetchEntries,
    retrieveContext,
    ingestContent: ingestContentApi,
    loading,
  } = useMemoryContext(userId);

  useEffect(() => {
    fetchStats();
    fetchEntries();
  }, [fetchStats, fetchEntries]);

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <p className="eyebrow">Memory Infrastructure</p>
          <h1>Compounding Memory Console</h1>
          <p className="subtle">Live view into ingestion, retrieval, and voice learning.</p>
        </div>
        <div className="dashboard__controls">
          <label>
            User ID
            <input value={userId} onChange={(event) => setUserId(event.target.value)} />
          </label>
          <button onClick={() => fetchStats()}>Refresh</button>
        </div>
      </header>

      <section className="dashboard__grid">
        <div className="card">
          <h2>Memory Stats</h2>
          {!stats ? (
            <p className="subtle">No stats yet. Ingest content to see metrics.</p>
          ) : (
            <div className="stats">
              <div>
                <p>Total Entries</p>
                <strong>{stats.total_entries}</strong>
              </div>
              <div>
                <p>Tokens Indexed</p>
                <strong>{stats.total_tokens_indexed}</strong>
              </div>
              <div>
                <p>Health Score</p>
                <strong>{stats.memory_health_score}</strong>
              </div>
              <div>
                <p>Voice Confidence</p>
                <strong>{stats.voice_profile_confidence.toFixed(2)}</strong>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <h2>Ingest Content</h2>
          <div className="ingest-form">
            <select value={ingestType} onChange={(event) => setIngestType(event.target.value)}>
              <option value="document">document</option>
              <option value="text_snippet">text_snippet</option>
              <option value="article">article</option>
              <option value="link">link</option>
              <option value="video">video</option>
            </select>
            <input
              placeholder="Title"
              value={ingestTitle}
              onChange={(event) => setIngestTitle(event.target.value)}
            />
            <input
              placeholder="Source URL (optional)"
              value={ingestSource}
              onChange={(event) => setIngestSource(event.target.value)}
            />
            <input
              placeholder="Tags (comma-separated)"
              value={ingestTags}
              onChange={(event) => setIngestTags(event.target.value)}
            />
            <textarea
              placeholder="Content to ingest"
              value={ingestContent}
              onChange={(event) => setIngestContent(event.target.value)}
            />
            <button
              onClick={() =>
                ingestContentApi({
                  content_type: ingestType,
                  title: ingestTitle || "Untitled",
                  content: ingestContent,
                  source_url: ingestSource || undefined,
                  tags: ingestTags
                    .split(",")
                    .map((tag) => tag.trim())
                    .filter(Boolean),
                })
              }
              disabled={loading || !ingestContent}
            >
              Ingest
            </button>
            {ingestResult && (
              <p className="subtle">Ingested {ingestResult.entry_id}</p>
            )}
          </div>
        </div>

        <div className="card">
          <h2>Context Preview</h2>
          <div className="context-form">
            <input value={query} onChange={(event) => setQuery(event.target.value)} />
            <button onClick={() => retrieveContext(query)} disabled={loading}>
              Retrieve
            </button>
          </div>
          <ContextPreview context={context} />
        </div>

        <div className="card full">
          <h2>Recent Memory</h2>
          <MemoryTimeline entries={entries} />
        </div>
      </section>
    </div>
  );
}
