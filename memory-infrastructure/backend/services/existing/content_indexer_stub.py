"""Content Indexer Stub - READ ONLY REFERENCE"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class IndexResult:
    doc_id: str
    embedding_id: str
    indexed_at: datetime
    token_count: int


class ContentIndexer:
    async def index_text_content(self, user_id: str, doc_id: str, content: str, metadata: dict) -> IndexResult:
        raise NotImplementedError("Use mock in tests")

    async def delete_indexed_content(self, user_id: str, doc_id: str) -> bool:
        raise NotImplementedError("Use mock in tests")
