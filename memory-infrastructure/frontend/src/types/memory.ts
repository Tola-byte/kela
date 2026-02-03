export type MemoryEntry = {
  id: string;
  user_id: string;
  content_type: string;
  title: string;
  content_preview: string;
  embedding_id: string;
  indexed_at: string;
  last_accessed_at?: string | null;
  access_count: number;
  relevance_decay: number;
  source_url?: string | null;
  source_metadata?: Record<string, unknown> | null;
  related_entries: string[];
  tags: string[];
};

export type MemoryStats = {
  user_id: string;
  total_entries: number;
  entries_by_type: Record<string, number>;
  total_tokens_indexed: number;
  memory_health_score: number;
  oldest_entry?: string | null;
  newest_entry?: string | null;
  voice_profile_confidence: number;
  last_compounding_run?: string | null;
};

export type ContextSource = {
  entry_id: string;
  title: string;
  content_type: string;
  relevance_score: number;
  excerpt: string;
  source_url?: string | null;
};

export type RetrievedContext = {
  query: string;
  sources: ContextSource[];
  context_text: string;
  token_count: number;
  voice_summary?: string | null;
  retrieval_time_ms: number;
  sources_considered: number;
  sources_included: number;
};
