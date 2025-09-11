from uuid import uuid4
from langchain.schema import Document
import re
from models.openai import OpenAIEmbedModel
from rag_engine.generate_answer import RAGLLM
from vector_store.adapt_db import return_vector_db


openai_embed_model = OpenAIEmbedModel()
vector_db =  return_vector_db(name = "qdrant",      #chroma or qdrant supported for now
                            collection_name = "rm_test3",      
                            embedding_model=openai_embed_model.model,
                            qdrant_url="http://localhost:6333/")

def extract_proposal_number(query):
    # Enhanced patterns to handle hyphens and various formats
    patterns = [
        r'\b([A-Z]{1,4}\d{2,6}-[A-Z]{1,6}\d{0,3})\b',     # AP112-REV1, ABC123-DEF2
        r'\b([A-Z]{1,4}\d{2,6}-[A-Z]{1,6})\b',            # AP112-REV, ABC123-DRAFT
        r'\b([A-Z]{1,3}\d{2,6}[A-Z]{0,3})\b',             # AP112DG (no hyphen)
        r'\b(\d{4,8}-[A-Z]{1,6}\d{0,3})\b',               # 1234-REV1, 567890-FINAL2
        r'\b([A-Z]{2,4}-\d{3,6}-[A-Z]{1,6})\b',           # PROJ-1234-REV
        r'\b([A-Z]{1,4}\d{1,6}-\d{1,4})\b',               # AP112-1, ABC12-25
        r'\b(\d{6,10})\b',                                 # Pure numbers: 123456
    ]
    
    query_upper = query.upper()
    
    for pattern in patterns:
        matches = re.findall(pattern, query_upper)
        if matches:
            return matches[0]
    
    return None


class ChatBot():
    def __init__(self):
        self.model = RAGLLM(str(uuid4()))
        self.retriever = vector_db.get_retriever(k = 4)


    async def run(self, query: str):
        try:
            transformed_query = await self.model.transform_query(query)
            print(f"{"--"*20} Transformed query {"--"*20}")
            print(transformed_query)
        except Exception as e:
            print("Exception in transforming the query:",e)
            raise
        try:
            metadata_filters = extract_proposal_number(transformed_query)
            if metadata_filters:
                proposal_number = metadata_filters.split('-')
                if (len(proposal_number) >=1) and (proposal_number[0] != ''):
                    proposal_number = proposal_number[0].strip()
                    print("--------------- PROPOSAL NUMBER IDENTIFICATION -----------------")
                    print(proposal_number)

                    retrieved_docs = await vector_db.filtered_similarity_search(transformed_query,proposal_number)
                    if len(retrieved_docs) == 0:
                        retrieved_docs = await self.retriever.ainvoke(transformed_query)
                else:
                    retrieved_docs = await self.retriever.ainvoke(transformed_query)

            else:
                retrieved_docs = await self.retriever.ainvoke(transformed_query)

        except Exception as e:
            print("Exception in Retrieving the documents::",e)
            raise

        expanded_docs = []
        final_context = ""

        for doc in retrieved_docs:
            print("------------------------- ORIGINAL CHUNK  -------------------")
            print(doc.page_content)
            print(doc.metadata)
           
            source = doc.metadata.get("source")
            chunk_number = doc.metadata.get("chunk_number")
            
            window_chunk_numbers = [chunk_number - 1, chunk_number, chunk_number + 1]
         
            windowed_chunks = await vector_db.get_docs_by_metadata({"source": source},
                                                                   window_chunk_numbers = window_chunk_numbers)
            expanded_docs.extend(windowed_chunks)
            
        expanded_docs.sort(key=lambda x: x.metadata.get('chunk_number', 0))
        print(expanded_docs)
        
        
        final_context += "\n".join([doc.page_content for doc in expanded_docs])
        final_context += "\n\n"

        print(" ----------------------------  FINAL CONTEXT --------------------------------------- ")
        print(final_context)
        res = await self.model.generate(query, final_context)

        metadata = {
            "sources": [{
                "source": doc.metadata.get("source", "Unknown"),
                "page": doc.metadata.get("page", "Unknown")
            } for doc in retrieved_docs]
        }

        return res, metadata
