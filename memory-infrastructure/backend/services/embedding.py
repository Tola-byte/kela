from __future__ import annotations

import random
from typing import Dict


class LocalVoyageClient:
    """Deterministic local embedding generator for offline usage."""

    def __init__(self, dimension: int = 512) -> None:
        self.dimension = dimension
        self._cache: Dict[str, list[float]] = {}

    async def embed(self, text: str) -> list[float]:
        if text not in self._cache:
            random.seed(hash(text))
            self._cache[text] = [random.gauss(0, 1) for _ in range(self.dimension)]
        return self._cache[text]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [await self.embed(text) for text in texts]

    async def embed_query(self, text: str) -> list[float]:
        return await self.embed(text)
