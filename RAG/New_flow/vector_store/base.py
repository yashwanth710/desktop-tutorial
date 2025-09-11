from abc import ABC, abstractmethod
from typing import List, Any
import os
import hashlib
from schemas.models import ChunkData


class BaseVectorStore(ABC):

    @abstractmethod
    async def add_chunks(self, chunks: List[ChunkData]):
        """add chunks to the underlying vector database."""

    @abstractmethod
    async def check_source_exists(self, source: str):
        """check if same pdf is ingested in db or not"""
       
    @abstractmethod
    async def get_docs_by_metadata(self, metadata_filter: dict):
        """"""

    def get_retriever(self, search_type: str = "similarity", k: int = 4):
        """Get retriever for the vector store."""
        return self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
   )

    def _generate_document_id(self, source_path: str) -> str:
        """
        Generate consistent document ID from source path.
        """
        # Normalize path and create hash for consistent ID
        normalized_path = os.path.normpath(source_path)
        return hashlib.md5(normalized_path.encode()).hexdigest()

    