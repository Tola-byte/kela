from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def estimate_token_count(text: str) -> int:
    # Rough heuristic: ~4 chars per token in English
    if not text:
        return 0
    return max(1, len(text) // 4)


def recency_score(created_at: datetime, now: datetime | None = None, half_life_days: int = 14) -> float:
    if not now:
        now = now_utc()
    delta = max((now - created_at).total_seconds(), 0)
    half_life_seconds = half_life_days * 86400
    if half_life_seconds <= 0:
        return 1.0
    return 0.5 ** (delta / half_life_seconds)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / ((norm_a ** 0.5) * (norm_b ** 0.5))
