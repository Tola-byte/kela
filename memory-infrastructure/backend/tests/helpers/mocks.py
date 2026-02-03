"""Mock implementations for testing."""

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class MockSearchResult:
    doc_id: str
    score: float
    payload: dict[str, Any]


class MockQdrantService:
    def __init__(self):
        self.collections: dict[str, dict[str, tuple[list[float], dict]]] = {}

    async def init_collection(self, user_id: str) -> bool:
        name = f"user_{user_id}"
        if name not in self.collections:
            self.collections[name] = {}
        return True

    async def upsert(self, user_id: str, doc_id: str, vector: list[float], payload: dict[str, Any]) -> bool:
        name = f"user_{user_id}"
        if name not in self.collections:
            await self.init_collection(user_id)
        self.collections[name][doc_id] = (vector, payload)
        return True

    async def search(
        self,
        user_id: str,
        query_vector: list[float],
        limit: int = 20,
        threshold: float = 0.5,
        type_filter: str | None = None,
    ) -> list[MockSearchResult]:
        name = f"user_{user_id}"
        if name not in self.collections:
            return []
        results = []
        for doc_id, (vector, payload) in self.collections[name].items():
            if type_filter and payload.get("type") != type_filter:
                continue
            score = self._cosine_similarity(query_vector, vector)
            if score >= threshold:
                results.append(MockSearchResult(doc_id=doc_id, score=score, payload=payload))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def delete(self, user_id: str, doc_id: str) -> bool:
        name = f"user_{user_id}"
        if name in self.collections and doc_id in self.collections[name]:
            del self.collections[name][doc_id]
            return True
        return False

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class MockVoyageClient:
    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self._cache: dict[str, list[float]] = {}

    async def embed(self, text: str) -> list[float]:
        if text not in self._cache:
            random.seed(hash(text))
            self._cache[text] = [random.gauss(0, 1) for _ in range(self.dimension)]
        return self._cache[text]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return await self.embed(text)


class MockVoiceProfileService:
    def __init__(self):
        self.profiles: dict[str, dict] = {}

    async def get_profile(self, user_id: str):
        return self.profiles.get(user_id)

    async def update_profile(self, user_id: str, new_content: str):
        if user_id not in self.profiles:
            self.profiles[user_id] = {"user_id": user_id, "sample_size": 0, "confidence": 0.0}
        self.profiles[user_id]["sample_size"] += 1
        self.profiles[user_id]["confidence"] = min(0.95, self.profiles[user_id]["confidence"] + 0.1)
        return self.profiles[user_id]
