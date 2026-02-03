from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from models import ContextRequest, ContextSource, RetrievedContext, VoiceContextRequest, VoiceContext
from services.app_services import context_builder
from services.factory import factory
from services.utils import estimate_token_count

router = APIRouter(prefix="/api/context", tags=["context"])


@router.post("/retrieve", response_model=RetrievedContext)
async def retrieve_context(
    request: ContextRequest,
    user_id: str = Query(..., min_length=1),
) -> RetrievedContext:
    return await context_builder.retrieve_context(user_id, request)


@router.post("/voice", response_model=VoiceContext)
async def get_voice_context(
    request: VoiceContextRequest,
    user_id: str = Query(..., min_length=1),
) -> VoiceContext:
    voice = await context_builder.build_voice_context(user_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return voice


@router.get("/suggest", response_model=list[ContextSource])
async def suggest_related_context(
    entry_id: str = Query(...),
    user_id: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=20),
) -> list[ContextSource]:
    query_vec = await factory.vector_store.get_vector(user_id, entry_id)
    if not query_vec:
        return []
    results = await factory.vector_store.search(
        user_id=user_id,
        query_vector=query_vec,
        limit=limit,
        threshold=0.5,
    )
    sources: list[ContextSource] = []
    for result in results:
        if result.doc_id == entry_id:
            continue
        entry = await factory.memory_store.get(user_id, result.doc_id)
        if not entry:
            continue
        sources.append(
            ContextSource(
                entry_id=entry.id,
                title=entry.title,
                content_type=entry.content_type,
                relevance_score=result.score,
                excerpt=entry.content_preview,
                source_url=entry.source_url,
            )
        )
    return sources


@router.post("/preview")
async def preview_context_injection(
    request: ContextRequest,
    prompt_template: str = Query(...),
    user_id: str = Query(..., min_length=1),
) -> dict:
    retrieved = await context_builder.retrieve_context(user_id, request)
    final_prompt = prompt_template.replace("{{context}}", retrieved.context_text).replace(
        "{{query}}", request.query
    )
    return {
        "final_prompt": final_prompt,
        "token_count": estimate_token_count(final_prompt),
        "sources_used": [source.entry_id for source in retrieved.sources],
    }
