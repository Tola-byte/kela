from __future__ import annotations

import time
from datetime import datetime, timedelta

from models import ContextRequest, ContextSource, RetrievedContext, VoiceContext
from .memory_store import MemoryStore
from .vector_store import LocalVectorStore
from .embedding import LocalVoyageClient
from .voice_profile_service import VoiceProfileService
from .utils import estimate_token_count, recency_score, now_utc


class ContextBuilder:
    def __init__(
        self,
        store: MemoryStore,
        vector_store: LocalVectorStore,
        embedding_client: LocalVoyageClient,
        voice_profile: VoiceProfileService,
    ) -> None:
        self.store = store
        self.vector_store = vector_store
        self.embedding_client = embedding_client
        self.voice_profile = voice_profile

    async def retrieve_context(self, user_id: str, request: ContextRequest) -> RetrievedContext:
        start = time.time()
        query_vec = await self.embedding_client.embed_query(request.query)
        results = await self.vector_store.search(
            user_id=user_id,
            query_vector=query_vec,
            limit=max(20, request.max_sources * 3),
            threshold=request.min_relevance,
        )

        sources_considered = len(results)
        sources: list[ContextSource] = []
        ranked = []
        now = now_utc()
        for result in results:
            entry = await self.store.get(user_id, result.doc_id)
            if not entry:
                continue
            if request.content_types and entry.content_type not in request.content_types:
                continue
            if request.recency_days:
                if entry.indexed_at < now - timedelta(days=request.recency_days):
                    continue
            recency = recency_score(entry.indexed_at, now=now)
            combined = 0.7 * result.score + 0.3 * recency
            ranked.append((combined, result, entry))

        ranked.sort(key=lambda x: x[0], reverse=True)
        total_tokens = 0
        if not ranked:
            records = await self.store.list(user_id, None, request.max_sources, 0, "indexed_at")
            for entry in records:
                excerpt = entry.content_preview
                token_cost = estimate_token_count(excerpt)
                if total_tokens + token_cost > request.max_tokens:
                    continue
                recency = recency_score(entry.indexed_at, now=now)
                sources.append(
                    ContextSource(
                        entry_id=entry.id,
                        title=entry.title,
                        content_type=entry.content_type,
                        relevance_score=recency,
                        excerpt=excerpt,
                        source_url=entry.source_url,
                    )
                )
                total_tokens += token_cost
            context_text = self._format_context(request, sources)
            voice_summary = None
            if request.include_voice_profile:
                profile = await self.voice_profile.get_profile(user_id)
                if profile:
                    voice_summary = f"Tone: {', '.join(profile.tone_keywords[:5])}. Confidence: {profile.confidence:.2f}"
            retrieval_time_ms = int((time.time() - start) * 1000)
            return RetrievedContext(
                query=request.query,
                sources=sources,
                context_text=context_text,
                token_count=total_tokens,
                voice_summary=voice_summary,
                retrieval_time_ms=retrieval_time_ms,
                sources_considered=sources_considered,
                sources_included=len(sources),
            )
        for combined_score, result, entry in ranked:
            excerpt = entry.content_preview
            token_cost = estimate_token_count(excerpt)
            if total_tokens + token_cost > request.max_tokens:
                continue
            sources.append(
                ContextSource(
                    entry_id=entry.id,
                    title=entry.title,
                    content_type=entry.content_type,
                    relevance_score=combined_score,
                    excerpt=excerpt,
                    source_url=entry.source_url,
                )
            )
            total_tokens += token_cost
            if len(sources) >= request.max_sources:
                break

        context_text = self._format_context(request, sources)
        voice_summary = None
        if request.include_voice_profile:
            profile = await self.voice_profile.get_profile(user_id)
            if profile:
                voice_summary = f"Tone: {', '.join(profile.tone_keywords[:5])}. Confidence: {profile.confidence:.2f}"

        retrieval_time_ms = int((time.time() - start) * 1000)
        return RetrievedContext(
            query=request.query,
            sources=sources,
            context_text=context_text,
            token_count=total_tokens,
            voice_summary=voice_summary,
            retrieval_time_ms=retrieval_time_ms,
            sources_considered=sources_considered,
            sources_included=len(sources),
        )

    async def build_voice_context(self, user_id: str) -> VoiceContext | None:
        profile = await self.voice_profile.get_profile(user_id)
        if not profile:
            return None
        return VoiceContext(
            profile_summary=f"User voice profile with {profile.sample_size} samples.",
            tone_guidance=", ".join(profile.tone_keywords[:5]),
            vocabulary_hints=profile.vocabulary_patterns.get("common_words", []),
            phrases_to_use=profile.vocabulary_patterns.get("preferred_phrases", []),
            things_to_avoid=profile.vocabulary_patterns.get("words_to_avoid", []),
            example_excerpts=[],
            confidence=profile.confidence,
        )

    def _format_context(self, request: ContextRequest, sources: list[ContextSource]) -> str:
        if request.format == "xml":
            parts = ["<context>"]
            for source in sources:
                parts.append(
                    f"  <source id=\"{source.entry_id}\" type=\"{source.content_type}\">\n"
                    f"    <title>{source.title}</title>\n"
                    f"    <excerpt>{source.excerpt}</excerpt>\n"
                    "  </source>"
                )
            parts.append("</context>")
            return "\n".join(parts)
        if request.format == "plain":
            return "\n\n".join(
                f"[{idx + 1}] {source.title} — {source.excerpt}" for idx, source in enumerate(sources)
            )
        return "\n\n".join(
            f"### {source.title}\n{source.excerpt}" for source in sources
        )
