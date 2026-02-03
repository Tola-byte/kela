from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict


@dataclass
class VoiceProfile:
    user_id: str
    tone_keywords: list[str]
    vocabulary_patterns: dict
    sentence_structure: dict
    script_pacing: dict
    storytelling_patterns: dict
    cta_style: dict
    sample_size: int
    confidence: float
    version: int
    created_at: datetime


class VoiceProfileService:
    """Lightweight local voice profile analyzer for demo purposes."""

    def __init__(self) -> None:
        self._profiles: Dict[str, VoiceProfile] = {}

    async def analyze_content(self, user_id: str, content: str) -> VoiceProfile:
        existing = self._profiles.get(user_id)
        if not existing:
            profile = self._build_profile(user_id, content, 1, 0.8)
            self._profiles[user_id] = profile
            return profile
        return await self.update_profile(user_id, content)

    async def update_profile(self, user_id: str, new_content: str) -> VoiceProfile:
        existing = self._profiles.get(user_id)
        if not existing:
            return await self.analyze_content(user_id, new_content)
        sample_size = existing.sample_size + 1
        confidence = min(0.95, existing.confidence + 0.1)
        merged = self._merge_profile(existing, new_content, sample_size, confidence)
        self._profiles[user_id] = merged
        return merged

    async def get_profile(self, user_id: str) -> VoiceProfile | None:
        return self._profiles.get(user_id)

    def _build_profile(self, user_id: str, content: str, sample_size: int, confidence: float) -> VoiceProfile:
        keywords = self._extract_keywords(content)
        return VoiceProfile(
            user_id=user_id,
            tone_keywords=keywords,
            vocabulary_patterns={
                "common_words": keywords[:5],
                "preferred_phrases": keywords[5:8],
                "words_to_avoid": [],
            },
            sentence_structure={"avg_length": "medium", "formality": "mixed", "grammar_style": "modern"},
            script_pacing={"hook_length": "short", "beat_pattern": "steady", "pause_placement": "balanced"},
            storytelling_patterns={
                "structure": "problem-solution",
                "transitions": ["next", "then", "finally"],
                "narrative_style": "insight-driven",
            },
            cta_style={"approach": "direct", "examples": ["Try this next.", "Let me know if you'd like a template."]},
            sample_size=sample_size,
            confidence=confidence,
            version=sample_size,
            created_at=datetime.now(timezone.utc),
        )

    def _merge_profile(
        self,
        existing: VoiceProfile,
        new_content: str,
        sample_size: int,
        confidence: float,
    ) -> VoiceProfile:
        new_keywords = self._extract_keywords(new_content)
        merged_keywords = list(dict.fromkeys(existing.tone_keywords + new_keywords))[:10]
        return VoiceProfile(
            user_id=existing.user_id,
            tone_keywords=merged_keywords,
            vocabulary_patterns={
                "common_words": merged_keywords[:5],
                "preferred_phrases": merged_keywords[5:8],
                "words_to_avoid": [],
            },
            sentence_structure=existing.sentence_structure,
            script_pacing=existing.script_pacing,
            storytelling_patterns=existing.storytelling_patterns,
            cta_style=existing.cta_style,
            sample_size=sample_size,
            confidence=confidence,
            version=sample_size,
            created_at=existing.created_at,
        )

    @staticmethod
    def _extract_keywords(content: str) -> list[str]:
        words = [w.strip(".,!?;:").lower() for w in content.split()]
        words = [w for w in words if len(w) > 4]
        counter = Counter(words)
        return [w for w, _ in counter.most_common(10)]
