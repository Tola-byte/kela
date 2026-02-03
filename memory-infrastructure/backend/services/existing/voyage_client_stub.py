"""
Voyage AI Client Stub - READ ONLY REFERENCE
"""


class VoyageClient:
    """Voyage AI embedding generation."""

    async def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Use mock in tests")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Use mock in tests")

    async def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("Use mock in tests")
