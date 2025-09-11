from langchain_chroma import Chroma
from langchain.schema import Document
from typing import List, Any
import os

from vector_store.base import BaseVectorStore
from schemas.models import ChunkData


class ChromaVectorDB(BaseVectorStore):
    def __init__(self,
                 collection_name : str,
                 persist_directory : str,
                 embedding_model):
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        os.makedirs(persist_directory, exist_ok= True)

        self.vector_store = Chroma(collection_name= collection_name,
                                   embedding_function=embedding_model,
                                   persist_directory=persist_directory)
        
        
    async def add_chunks(self, chunks: List[ChunkData]):
        if not chunks:
            return
            
        source = chunks[0].metadata["source"]   #checking source from first chunk only, need to modify this function
       
        if await self.check_source_exists(source):
            raise ValueError(f"Source {source} already exists in the vector database.")
        
        documents = []
        doc_ids = []
        
        for i, chunk in enumerate(chunks):
            doc_id = f"{self._generate_document_id(source)}_{i}"
            doc_ids.append(doc_id)
            metadata = chunk.metadata.copy()
            metadata['doc_id'] = doc_id
            
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

    async def get_docs_by_metadata(self, metadata_filter: dict, window_chunk_numbers:List[int]):
       
        results = self.vector_store.get(where=metadata_filter)
        
        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        # Fallback if metadata is missing (e.g., None or empty)
        if not metadatas or len(metadatas) != len(documents):
            metadatas = [{} for _ in documents]  # Default empty metadata

        windowed_chunks = []
        
        for doc, metadata in zip(documents, metadatas):
            if metadata.get("chunk_number") in window_chunk_numbers:
                windowed_chunks.append(Document(page_content = doc,
                                                metadata = metadata))

        return windowed_chunks
    
    async def check_source_exists(self, source: str):
      
        try:
            results = self.vector_store.get(where={"source": source})
            return True if results['documents'] else False
        except Exception as e:
            print(f"Following error in checking source exists: {e}")
            raise

        

