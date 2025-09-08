# import streamlit as st
# from typing import List, Dict, Tuple

# from config.settings import settings
# from processors.pdf_processor import PDFProcessor
# from database.qdrant_manager import QdrantManager
# from ai.azure_client import AzureOpenAIClientREST as AzureOpenAIClient
# from utils.health_check import check_qdrant_connection, get_qdrant_info


# class RAGChatbot:
#     def __init__(self):
#         self.pdf_processor = PDFProcessor(chunk_size=500, chunk_overlap=50)
#         self.qdrant_manager = QdrantManager()
#         self.azure_client = AzureOpenAIClient()
#         self.processed_documents = set()
    
#     def process_and_store_pdf(self, pdf_bytes: bytes, document_id: str):
#         """Process PDF and store in Qdrant"""
#         if document_id in self.processed_documents:
#             st.info("PDF already processed. Using existing data.")
#             return
        
#         with st.spinner("Processing PDF..."):
#             # Process PDF
#             chunks = self.pdf_processor.process_pdf(pdf_bytes)
            
#             if not chunks:
#                 st.error("No text could be extracted from the PDF.")
#                 return
            
#             # Get embeddings
#             embeddings = []
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             for i, chunk in enumerate(chunks):
#                 status_text.text(f"Generating embeddings... ({i+1}/{len(chunks)})")
#                 embedding = self.azure_client.get_embedding(chunk['text'])
#                 if embedding:
#                     embeddings.append(embedding)
#                 progress_bar.progress((i + 1) / len(chunks))
            
#             status_text.empty()
#             progress_bar.empty()
            
#             if embeddings:
#                 # Create collection with appropriate embedding size
#                 self.qdrant_manager.create_collection(len(embeddings[0]))
                
#                 # Store in Qdrant
#                 self.qdrant_manager.store_chunks(chunks, embeddings)
#                 self.processed_documents.add(document_id)
                
#                 st.success(f"✅ Processed {len(chunks)} chunks from the PDF.")
#             else:
#                 st.error("Failed to generate embeddings for the PDF content.")
    
#     def get_answer(self, query: str, chat_history: List[Dict]) -> Tuple[str, List[Dict]]:
#         """Get answer for query"""
#         # Get query embedding
#         query_embedding = self.azure_client.get_embedding(query)
#         if not query_embedding:
#             return "Error generating embedding.", []
        
#         # Search for similar chunks
#         similar_chunks = self.qdrant_manager.search_similar(query_embedding)
#         if not similar_chunks:
#             return "No relevant information found in the document.", []
        
#         # Build context
#         context = "\n\n".join([
#             f"Page {chunk['page_number']}: {chunk['text']}" + 
#             (" [Contains visual elements]" if chunk['has_visuals'] else "")
#             for chunk in similar_chunks
#         ])
        
#         # Generate response
#         response = self.azure_client.generate_response(query, context, chat_history)
        
#         # Prepare sources
#         sources = [
#             {
#                 'page': chunk['page_number'],
#                 'text_preview': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
#                 'has_visuals': chunk['has_visuals'],
#                 'relevance_score': chunk['score']
#             }
#             for chunk in similar_chunks
#         ]
        
#         return response, sources


# def display_system_status():
#     """Display system status in sidebar"""
#     with st.sidebar:
#         st.header("🔧 System Status")
        
#         # Check Qdrant connection
#         qdrant_connected, qdrant_message = check_qdrant_connection()
#         if qdrant_connected:
#             st.success("✅ Qdrant: Connected")
            
#             # Show collection info
#             qdrant_info = get_qdrant_info()
#             if qdrant_info['status'] == 'connected':
#                 st.info(f"📊 Collections: {qdrant_info['collections_count']}")
#                 # Removed collection list
#         else:
#             st.error(f"❌ Qdrant: {qdrant_message}")
#             st.info("💡 Run: ./start_qdrant.sh to start Qdrant")
        
#         st.markdown("---")


# def main():
#     st.set_page_config(
#         page_title="PDF RAG Chatbot",
#         page_icon="📄",
#         layout="wide"
#     )
    
#     st.title("📄 PDF RAG Chatbot")
#     st.markdown("Upload a PDF and ask questions about its content!")
    
#     # Initialize session state
#     if 'chat_history' not in st.session_state:
#         st.session_state.chat_history = []
#     if 'rag_bot' not in st.session_state:
#         st.session_state.rag_bot = RAGChatbot()
#     if 'current_document' not in st.session_state:
#         st.session_state.current_document = None
    
#     # Sidebar for PDF upload
#     with st.sidebar:
#         st.header("📁 Upload PDF")
#         uploaded_file = st.file_uploader(
#             "Choose a PDF file",
#             type="pdf",
#             help="Upload a PDF file to start chatting about its content"
#         )
        
#         if uploaded_file:
#             if st.session_state.current_document != uploaded_file.name:
#                 st.session_state.current_document = uploaded_file.name
#                 st.session_state.chat_history = []
                
#                 # Process PDF
#                 pdf_bytes = uploaded_file.read()
#                 st.session_state.rag_bot.process_and_store_pdf(
#                     pdf_bytes, 
#                     uploaded_file.name
#                 )
        
#         # Display system status
#         display_system_status()
    
#     # Main chat interface
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.header("💬 Chat")

#         # Chat input at the top (only one instance)
#         prompt = st.chat_input("Ask a question about the PDF...", key="chat_prompt")

#         # If user asks a question
#         if prompt:
#             if not st.session_state.current_document:
#                 st.warning("Please upload a PDF first!")
#             else:
#                 # Add user message
#                 st.session_state.chat_history.append({"role": "user", "content": prompt})
                
#                 # Get response
#                 with st.spinner("Thinking..."):
#                     response, sources = st.session_state.rag_bot.get_answer(
#                         prompt, 
#                         st.session_state.chat_history
#                     )
                
#                 # Save assistant response
#                 st.session_state.chat_history.append({
#                     "role": "assistant", 
#                     "content": response,
#                     "sources": sources
#                 })
        
#         # Display chat history (only this section should display messages)
#         for message in st.session_state.chat_history:
#             with st.chat_message(message["role"]):
#                 st.markdown(message["content"])
#                 if message["role"] == "assistant" and "sources" in message:
#                     with st.expander("📚 View Sources"):
#                         for source in message["sources"]:
#                             st.write(f"**Page {source['page']}** (Relevance: {source['relevance_score']:.3f})")
#                             st.caption(source['text_preview'])
#                             if source['has_visuals']:
#                                 st.info("Contains visual elements")
    
#     with col2:
#         st.header("📊 Document Info")
#         if st.session_state.current_document:
#             st.success(f"✅ **Current Document:** {st.session_state.current_document}")
#             st.info(f"💬 **Chat Messages:** {len([m for m in st.session_state.chat_history if m['role'] == 'user'])}")
            
#             # Show processing status
#             if st.session_state.current_document in st.session_state.rag_bot.processed_documents:
#                 st.success("✅ Document processed successfully")
#             else:
#                 st.warning("⏳ Document processing required")
#         else:
#             st.warning("No document uploaded")
        
#         st.markdown("---")
#         st.header("⚙️ How it works")
#         st.markdown("""
#         1. **Upload PDF** - Document is processed page by page  
#         2. **Text Extraction** - Text is extracted using multiple methods  
#         3. **Visual Detection** - Diagrams and tables are identified  
#         4. **Vector Storage** - Content is stored in QdrantDB  
#         5. **Smart Search** - Relevant content is retrieved for questions  
#         6. **Accurate Answers** - Responses are based strictly on PDF content  
#         """)


# if __name__ == "__main__":
#     main()

import streamlit as st
from typing import List, Dict, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

from config.settings import settings
from processors.pdf_processor import PDFProcessor
from database.qdrant_manager import QdrantManager
from ai.azure_client import AzureOpenAIClientREST as AzureOpenAIClient
from utils.health_check import check_qdrant_connection, get_qdrant_info


class RAGChatbot:
    def __init__(self):
        self.pdf_processor = PDFProcessor(chunk_size=500, chunk_overlap=50)
        self.qdrant_manager = QdrantManager()
        self.azure_client = AzureOpenAIClient()
        self.processed_documents = set()
        self.embedding_executor = ThreadPoolExecutor(max_workers=5)
    
    async def process_and_store_pdf(self, pdf_bytes: bytes, document_id: str):
        """Process PDF and store in Qdrant asynchronously"""
        if document_id in self.processed_documents:
            st.info("PDF already processed. Using existing data.")
            return
        
        with st.spinner("Processing PDF..."):
            # Process PDF asynchronously
            chunks = await self.pdf_processor.process_pdf(pdf_bytes)
            
            if not chunks:
                st.error("No text could be extracted from the PDF.")
                return
            
            # Get embeddings asynchronously
            embeddings = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Process embeddings in batches for better performance
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                status_text.text(f"Generating embeddings... ({min(i + batch_size, len(chunks))}/{len(chunks)})")
                
                # Get embeddings for batch
                batch_embeddings = await asyncio.gather(*[
                    self.get_embedding_async(chunk['text']) for chunk in batch
                ])
                
                # Filter out None results
                valid_embeddings = [emb for emb in batch_embeddings if emb]
                embeddings.extend(valid_embeddings)
                
                progress_bar.progress(min((i + batch_size) / len(chunks), 1.0))
            
            status_text.empty()
            progress_bar.empty()
            
            if embeddings:
                # Create collection with appropriate embedding size
                self.qdrant_manager.create_collection(len(embeddings[0]))
                
                # Store in Qdrant
                self.qdrant_manager.store_chunks(chunks, embeddings)
                self.processed_documents.add(document_id)
                
                st.success(f"✅ Processed {len(chunks)} chunks from the PDF.")
            else:
                st.error("Failed to generate embeddings for the PDF content.")
    
    async def get_embedding_async(self, text: str):
        """Get embedding asynchronously using thread pool"""
        loop = asyncio.get_event_loop()
        try:
            embedding = await loop.run_in_executor(
                self.embedding_executor, 
                self.azure_client.get_embedding, 
                text
            )
            return embedding
        except Exception as e:
            st.error(f"Error generating embedding: {e}")
            return None
    
    def get_answer(self, query: str, chat_history: List[Dict]) -> Tuple[str, List[Dict]]:
        """Get answer for query"""
        # Get query embedding
        query_embedding = self.azure_client.get_embedding(query)
        if not query_embedding:
            return "Error generating embedding.", []
        
        # Search for similar chunks
        similar_chunks = self.qdrant_manager.search_similar(query_embedding)
        if not similar_chunks:
            return "No relevant information found in the document.", []
        
        # Build context
        context = "\n\n".join([
            f"Page {chunk['page_number']}: {chunk['text']}" + 
            (" [Contains visual elements]" if chunk['has_visuals'] else "")
            for chunk in similar_chunks
        ])
        
        # Generate response
        response = self.azure_client.generate_response(query, context, chat_history)
        
        # Prepare sources
        sources = [
            {
                'page': chunk['page_number'],
                'text_preview': chunk['text'][:100] + "..." if len(chunk['text']) > 100 else chunk['text'],
                'has_visuals': chunk['has_visuals'],
                'relevance_score': chunk['score']
            }
            for chunk in similar_chunks
        ]
        
        return response, sources
    
    def cleanup(self):
        """Clean up resources"""
        self.embedding_executor.shutdown(wait=False)


def display_system_status():
    """Display system status in sidebar"""
    with st.sidebar:
        st.header("🔧 System Status")
        
        # Check Qdrant connection
        qdrant_connected, qdrant_message = check_qdrant_connection()
        if qdrant_connected:
            st.success("✅ Qdrant: Connected")
            
            # Show collection info
            qdrant_info = get_qdrant_info()
            if qdrant_info['status'] == 'connected':
                st.info(f"📊 Collections: {qdrant_info['collections_count']}")
                # Removed collection list
        else:
            st.error(f"❌ Qdrant: {qdrant_message}")
            st.info("💡 Run: ./start_qdrant.sh to start Qdrant")
        
        st.markdown("---")


async def main_async():
    st.set_page_config(
        page_title="PDF RAG Chatbot",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 PDF RAG Chatbot")
    st.markdown("Upload a PDF and ask questions about its content!")
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'rag_bot' not in st.session_state:
        st.session_state.rag_bot = RAGChatbot()
    if 'current_document' not in st.session_state:
        st.session_state.current_document = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Sidebar for PDF upload
    with st.sidebar:
        st.header("📁 Upload PDF")
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type="pdf",
            help="Upload a PDF file to start chatting about its content"
        )
        
        if uploaded_file:
            if st.session_state.current_document != uploaded_file.name:
                st.session_state.current_document = uploaded_file.name
                st.session_state.chat_history = []
                st.session_state.processing_complete = False
                
                # Process PDF asynchronously
                pdf_bytes = uploaded_file.read()
                await st.session_state.rag_bot.process_and_store_pdf(pdf_bytes, uploaded_file.name)
                st.session_state.processing_complete = True
                st.rerun()
        
        # Display system status
        display_system_status()
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat")

        # Show processing status
        if st.session_state.current_document and not st.session_state.processing_complete:
            st.info("🔄 PDF is being processed. Please wait...")
        
        # Only show chat input when processing is complete
        if st.session_state.processing_complete or not st.session_state.current_document:
            # Chat input at the top
            prompt = st.chat_input("Ask a question about the PDF...", key="chat_prompt")

            # If user asks a question
            if prompt:
                if not st.session_state.current_document:
                    st.warning("Please upload a PDF first!")
                else:
                    # Add user message
                    st.session_state.chat_history.append({"role": "user", "content": prompt})
                    
                    # Get response
                    with st.spinner("Thinking..."):
                        response, sources = st.session_state.rag_bot.get_answer(
                            prompt, 
                            st.session_state.chat_history
                        )
                    
                    # Save assistant response
                    st.session_state.chat_history.append({
                        "role": "assistant", 
                        "content": response,
                        "sources": sources
                    })
                    st.rerun()
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📚 View Sources"):
                        for source in message["sources"]:
                            st.write(f"**Page {source['page']}** (Relevance: {source['relevance_score']:.3f})")
                            st.caption(source['text_preview'])
                            if source['has_visuals']:
                                st.info("Contains visual elements")
    
    with col2:
        st.header("📊 Document Info")
        if st.session_state.current_document:
            st.success(f"✅ **Current Document:** {st.session_state.current_document}")
            st.info(f"💬 **Chat Messages:** {len([m for m in st.session_state.chat_history if m['role'] == 'user'])}")
            
            # Show processing status
            if st.session_state.current_document in st.session_state.rag_bot.processed_documents:
                st.success("✅ Document processed successfully")
            else:
                st.warning("⏳ Document processing in progress...")
        else:
            st.warning("No document uploaded")
        
        st.markdown("---")
        st.header("⚙️ How it works")
        st.markdown("""
        1. **Upload PDF** - Document is processed page by page  
        2. **Text Extraction** - Text is extracted using multiple methods  
        3. **Visual Detection** - Diagrams and tables are identified  
        4. **Vector Storage** - Content is stored in QdrantDB  
        5. **Smart Search** - Relevant content is retrieved for questions  
        6. **Accurate Answers** - Responses are based strictly on PDF content  
        """)


def main():
    # Use asyncio to run the async main function
    asyncio.run(main_async())


if __name__ == "__main__":
    main()