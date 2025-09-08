from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid
import streamlit as st

from config.settings import settings

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self.collection_name = "pdf_documents"
        
    def create_collection(self, embedding_size: int):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            if self.collection_name not in [col.name for col in collections.collections]:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=embedding_size,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            st.error(f"Collection creation error: {e}")
    
    def store_chunks(self, chunks: list[dict], embeddings: list[list[float]]):
        """Store chunks with embeddings in Qdrant"""
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'text': chunk['text'],
                    'page_number': chunk['page_number'],
                    'has_visuals': chunk['has_visuals'],
                    'chunk_id': chunk['chunk_id']
                }
            ))
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        except Exception as e:
            st.error(f"Storage error: {e}")
    
    def search_similar(self, query_embedding: list[float], limit: int = None) -> list[dict]:
        """Search for similar chunks"""
        if limit is None:
            limit = settings.SEARCH_LIMIT
            
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit
            )
            
            return [{
                'text': hit.payload['text'],
                'page_number': hit.payload['page_number'],
                'has_visuals': hit.payload.get('has_visuals', False),
                'score': hit.score
            } for hit in results]
        except Exception as e:
            st.error(f"Search error: {e}")
            return []