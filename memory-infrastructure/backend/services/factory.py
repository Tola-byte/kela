from __future__ import annotations

from pathlib import Path

from .embedding import LocalVoyageClient
from .memory_store import MemoryStore
from .vector_store import LocalVectorStore
from .voice_profile_service import VoiceProfileService


class ServiceFactory:
    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        db_path = base_dir / "memory.db"
        self.memory_store = MemoryStore(db_path)
        self.vector_store = LocalVectorStore()
        self.embedding_client = LocalVoyageClient()
        self.voice_profile_service = VoiceProfileService()


factory = ServiceFactory()
