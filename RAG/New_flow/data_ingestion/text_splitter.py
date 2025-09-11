from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

from schemas.models import ChunkData, FullPageData


class TextSplitter():
    def __init__(self,
                 chunk_size : int = 1024,
                 chunk_overlap : int = 256,
                 min_chunk_size : int = 30):
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size,
                                                       chunk_overlap = chunk_overlap,
                                                       )
        
    
    async def split_page_data(self,document:FullPageData) -> List[ChunkData]:
        
        page_chunks = []
        text_content = document.content.strip()
        if not text_content:
            return []
        try:
            # if text data is already with in specified chunk size return as it is.
            if len(text_content) <= self.chunk_size:
                return [ChunkData(content=text_content, metadata=document.metadata.copy())]

            
            text_chunks = self.splitter.split_text(text_content)
            
            for chunk in text_chunks:
                if len(chunk.strip()) > self.min_chunk_size:
                    page_chunks.append(ChunkData(content = chunk.strip(),
                                                metadata = document.metadata.copy()))
                    
            return page_chunks
        except Exception as split_error:
            print(f"Error in splitting page data: {split_error}")
            raise 
    
    async def split_documents(self, documents: List[Dict[str, Any]]) ->List[ChunkData]:
        """
        Accepts a list of parsed PDF documents (output from PDFParser.extract_content)
        and returns a combined list of text and table row chunks.
        """
        final_chunks = []
        chunk_seq = 0
        try:
            for document in documents:
                page_data = document.get("text")
                if page_data:
                    text_chunks = await self.split_page_data(page_data)
                    for i, chunk in enumerate(text_chunks):
                        chunk.metadata["chunk_number"] = chunk_seq + i + 1
                    chunk_seq += len(text_chunks)
                    final_chunks.extend(text_chunks)

            return final_chunks
        except Exception as split_page_error:
            print(f"Error in splitting documents: {split_page_error}")
            raise 


        

        

        


