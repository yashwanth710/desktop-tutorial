from langchain_qdrant import QdrantVectorStore
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny
from qdrant_client.models import Distance, VectorParams
from typing import List, Any
import os
from uuid import uuid4

from vector_store.base import BaseVectorStore
from schemas.models import ChunkData



class QdrantVectorDB(BaseVectorStore):
    def __init__(self,
                 collection_name:str,
                 embedding_model,
                 qdrant_url:str):
        
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient(url = qdrant_url)
       
        
        try:
            self.vector_store = QdrantVectorStore.from_existing_collection(collection_name = collection_name,
                                              url = qdrant_url,
                                              embedding = embedding_model)
        except UnexpectedResponse as no_collection_error:
            if no_collection_error.status_code == 404:
                #given collection name is not exist in the db. so create it.
                embedding_dim = 3072
                self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE))

                self.vector_store = QdrantVectorStore(collection_name = collection_name,
                                                      client = self.qdrant_client,
                                                      embedding = embedding_model)
                
            else:
                print(f"Exception in vector db initialization: {no_collection_error}")
                raise
        except Exception as e:
            print(f"Exception in vector db initialization: {e}")
            raise

        

    async def add_chunks(self, chunks: List[ChunkData]):
        if not chunks:
            return
            
        source = chunks[0].metadata["source"]   #checking source from first chunk only, need to modify this function
        if await self.check_source_exists(source):
            raise ValueError(f"Source {source} already exists in the vector database.")
        
        documents = []
        doc_ids = [str(uuid4()) for _ in range(len(chunks))]
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.metadata.copy()
            metadata['doc_id'] = doc_ids[i]
            
            # Ensure metadata is serializable because most vector db take only either of these datatypes.
            cleaned_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    cleaned_metadata[key] = value
                else:
                    cleaned_metadata[key] = str(value)
            
            doc = Document(
                page_content=chunk.content,
                metadata=cleaned_metadata
            )
            print(doc)
            print("--"*35)
            documents.append(doc)
        
        # Add all documents
        self.vector_store.add_documents(
            documents=documents,
            ids=doc_ids
        )
        
        print(f"Added {len(documents)} chunks to vector database")

   
    async def check_source_exists(self, source: str):
        """check if same pdf is ingested in db or not"""
        try:
            filter = Filter(must=[FieldCondition(key="metadata.source",
                                                    match=MatchValue(value=source))
                                    ])

            count_result = self.qdrant_client.count(
                collection_name= self.collection_name,
                count_filter=filter)
            
            exists = count_result.count > 0
            return exists
        except Exception as e:
            print(f"Exception checking source exists {e}")
            raise


    async def get_docs_by_metadata(self, metadata_filter: dict,window_chunk_numbers:List[int]):
    
        # Convert metadata_filter dict to Qdrant filter format.
        conditions = []
        for key, value in metadata_filter.items():
            conditions.append(
                FieldCondition(
                    key=f"metadata.{key}",
                    match=MatchValue(value=value)
                )
            )
        if window_chunk_numbers:
            conditions.append(
            FieldCondition(
                key="metadata.chunk_number",
                match=MatchAny(any=window_chunk_numbers)
            )
        )
        
        filter_condition = Filter(must=conditions) if conditions else None
        
        # Search with filter, return all matching documents
        results = self.qdrant_client.scroll(
            collection_name=self.collection_name,
            scroll_filter=filter_condition,
            limit=200,
            with_payload=True,
            with_vectors=False
        )
        
        documents = []
        metadatas = []
        
        for point in results[0]:  # results[0] contains the points
            # Extract document content from payload
            content = point.payload.get(self.vector_store.content_payload_key, "")
            documents.append(content)
            
            # Extract metadata from payload
            metadata = point.payload.get(self.vector_store.metadata_payload_key, {})
            metadatas.append(metadata)
        
        # Fallback if metadata is missing (e.g., None or empty)
        if not metadatas or len(metadatas) != len(documents):
            metadatas = [{} for _ in documents]  # Default empty metadata

        return [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(documents, metadatas)
        ]
    
  
    async def filtered_similarity_search(self, query: str, proposal_number: str, k: int = 5):
        """
        """
        try:
            
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="metadata.proposal_number",
                        match=MatchValue(value=proposal_number)
                    )
                ]
            )
            
            # Use LangChain's similarity_search with filter
            # This ensures EXACT same return format as retriever.ainvoke()
            results = await self.vector_store.asimilarity_search(
                query=query,
                k=k,
                filter=qdrant_filter  # Pass Qdrant filter object
            )
            
            return results  # Guaranteed same format as retriever.ainvoke()
            
        except Exception as e:
            print(f"Filtered search error: {e}")
            raise