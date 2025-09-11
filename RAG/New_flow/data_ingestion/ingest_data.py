import os
import logging

from data_ingestion.pdf_parser import PDFParser
from data_ingestion.text_splitter import TextSplitter
#from data_ingestion.vector_ingestion import ChromaVectorDB
from models.openai import OpenAIEmbedModel
from vector_store.qdrant_db import QdrantVectorDB
from vector_store.adapt_db import return_vector_db



pdf_parser = PDFParser()
text_splitter = TextSplitter(chunk_size = 1024,
                            chunk_overlap = 256)
openai_embed_model = OpenAIEmbedModel()
ingestion_logger = logging.getLogger("ingestion")
"""
vector_db = return_vector_db(name = "chroma",       
                             collection_name = "rag_test",
                             persist_directory="./chroma_db",
                             embedding_model=openai_embed_model.model)
"""
vector_db =  return_vector_db(name = "qdrant",      #chroma or qdrant supported for now
                            collection_name = "rm_test3",      
                            embedding_model=openai_embed_model.model,
                            qdrant_url="http://localhost:6333/")
                            
async def save_document_data(document_path:str, actual_source:str):
    ingestion_logger.debug(f"processing file: {actual_source}")
    for file in os.listdir(document_path):
        #checking source already exists or not before doing parsing for saving openai token usage, computational cost so does time.
        if await vector_db.check_source_exists(actual_source):
            print("Source already exists in vector db. so skipping")
            return None
        page_documents = await pdf_parser.extract_content(os.path.join(document_path, file), source=actual_source)
        all_chunked_docs = await text_splitter.split_documents(page_documents)
        await vector_db.add_chunks(all_chunked_docs)
        print(f"Processed file: {file}")
   
 