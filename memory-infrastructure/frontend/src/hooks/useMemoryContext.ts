import { useCallback, useState } from "react";
import type { MemoryEntry, MemoryStats, RetrievedContext } from "../types/memory";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type IngestPayload = {
  content_type: string;
  title: string;
  content: string;
  source_url?: string;
  tags?: string[];
};

export function useMemoryContext(userId: string) {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [context, setContext] = useState<RetrievedContext | null>(null);
  const [ingestResult, setIngestResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`${apiBase}/api/memory/stats?user_id=${userId}`);
    const data = (await res.json()) as MemoryStats;
    setStats(data);
    setLoading(false);
  }, [userId]);

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`${apiBase}/api/memory/entries?user_id=${userId}&limit=20`);
    const data = (await res.json()) as MemoryEntry[];
    setEntries(data);
    setLoading(false);
  }, [userId]);

  const retrieveContext = useCallback(
    async (query: string) => {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/context/retrieve?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, max_tokens: 800, max_sources: 4, format: "markdown" }),
      });
      const data = (await res.json()) as RetrievedContext;
      setContext(data);
      setLoading(false);
    },
    [userId]
  );

  const ingestContent = useCallback(
    async (payload: IngestPayload) => {
      setLoading(true);
      const res = await fetch(`${apiBase}/api/memory/ingest?user_id=${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setIngestResult(data);
      await fetchStats();
      await fetchEntries();
      setLoading(false);
    },
    [userId, fetchStats, fetchEntries]
  );

  return { stats, entries, context, ingestResult, fetchStats, fetchEntries, retrieveContext, ingestContent, loading };
}
