"""Voice Profile Service Stub - READ ONLY REFERENCE"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class VocabularyPatterns:
    common_words: list[str]
    preferred_phrases: list[str]
    words_to_avoid: list[str]


@dataclass
class SentenceStructure:
    avg_length: str
    formality: str
    grammar_style: str


@dataclass
class ScriptPacing:
    hook_length: str
    beat_pattern: str
    pause_placement: str


@dataclass
class StorytellingPatterns:
    structure: str
    transitions: list[str]
    narrative_style: str


@dataclass
class CTAStyle:
    approach: str
    examples: list[str]


@dataclass
class VoiceProfile:
    user_id: str
    tone_keywords: list[str]
    vocabulary_patterns: VocabularyPatterns
    sentence_structure: SentenceStructure
    script_pacing: ScriptPacing
    storytelling_patterns: StorytellingPatterns
    cta_style: CTAStyle
    sample_size: int
    confidence: float
    version: int
    created_at: datetime


class VoiceProfileService:
    async def analyze_content(self, user_id: str, content: str) -> VoiceProfile:
        raise NotImplementedError("Use mock in tests")

    async def update_profile(self, user_id: str, new_content: str) -> VoiceProfile:
        raise NotImplementedError("Use mock in tests")

    async def get_profile(self, user_id: str) -> VoiceProfile | None:
        raise NotImplementedError("Use mock in tests")
