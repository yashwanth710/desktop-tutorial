# from openai import AzureOpenAI
# import streamlit as st

# from config.settings import settings

# class AzureOpenAIClient:
#     def __init__(self):
#         self.client = AzureOpenAI(
#             api_key=settings.AZURE_OPENAI_API_KEY,
#             api_version=settings.AZURE_OPENAI_API_VERSION,
#             azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
#         )
    
#     def get_embedding(self, text: str) -> list[float]:
#         """Get embedding for text"""
#         try:
#             response = self.client.embeddings.create(
#                 input=text,
#                 model=settings.AZURE_EMBEDDING_DEPLOYMENT
#             )
#             return response.data[0].embedding
#         except Exception as e:
#             st.error(f"Embedding error: {e}")
#             return []
    
#     def generate_response(self, query: str, context: str, chat_history: list[dict]) -> str:
#         """Generate response using Azure OpenAI"""
#         try:
#             # Build messages with context and history
#             messages = [
#                 {
#                     "role": "system",
#                     "content": """You are a helpful assistant that answers questions based strictly on the provided context.
#                     If the context doesn't contain the answer, say "I don't have enough information to answer that question."
#                     For visual elements like diagrams or tables, provide a detailed text explanation.
#                     Do not repeat answers. Keep responses concise and accurate."""
#                 }
#             ]
            
#             # Add chat history
#             for msg in chat_history[-settings.MAX_HISTORY_MESSAGES:]:
#                 messages.append(msg)
            
#             # Add current context and query
#             messages.extend([
#                 {
#                     "role": "user",
#                     "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer based strictly on the context:"
#                 }
#             ])
            
#             response = self.client.chat.completions.create(
#                 model=settings.AZURE_LLM_DEPLOYMENT,
#                 messages=messages,
#                 max_tokens=500,
#                 temperature=0.1
#             )
            
#             return response.choices[0].message.content.strip()
        
#         except Exception as e:
#             st.error(f"Response generation error: {e}")
#             return "Sorry, I encountered an error while generating the response."

import requests
import json

# ----------------------------
# Deployment URLs and Key
# ----------------------------
AZURE_OPENAI_API_KEY = "5Xz4qzHJIM5gveRUM9pr30iHKWxkT1gw4l0HORcKSTzzjObbnMqNJQQJ99BFACHYHv6XJ3w3AAABACOGxLfq"

# Choose which chat deployment you want
DEPLOYMENT_URL_CHAT = "https://rmes-openai-services.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
DEPLOYMENT_URL_EMBEDDING = "https://rmes-openai-services.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15"

HEADERS = {
    "Content-Type": "application/json",
    "api-key": AZURE_OPENAI_API_KEY
}

# ----------------------------
# Client
# ----------------------------
class AzureOpenAIClientREST:
    def get_embedding(self, text: str) -> list[float]:
        """Get embedding for a given text"""
        payload = {"input": text}
        try:
            resp = requests.post(DEPLOYMENT_URL_EMBEDDING, headers=HEADERS, data=json.dumps(payload))
            resp.raise_for_status()
            embedding = resp.json()["data"][0]["embedding"]
            return embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            return []

    def generate_response(self, query: str, context: str, chat_history: list[dict] = None) -> str:
        """Generate response using Azure OpenAI REST API"""
        if chat_history is None:
            chat_history = []

        # Build messages
        messages = [{"role": "system", "content": """You are a helpful assistant that answers questions strictly based on the provided context.
        If the context doesn't contain the answer, say "I don't have enough information to answer that question."
        For visual elements like diagrams or tables, provide a detailed text explanation.
        Do not repeat answers. Keep responses concise and accurate."""}]
        
        # Append chat history
        messages.extend(chat_history[-5:])  # Use last 5 messages
        
        # Add current query with context
        messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {query}\n\nAnswer based strictly on the context:"
        })

        payload = {
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.1
        }

        try:
            resp = requests.post(DEPLOYMENT_URL_CHAT, headers=HEADERS, data=json.dumps(payload))
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "Sorry, I encountered an error while generating the response."

# # ----------------------------
# # Example usage
# # ----------------------------
# client = AzureOpenAIClientREST()

# # Test embedding
# embedding = client.get_embedding("Hello world!")
# print("Embedding length:", len(embedding))

# # Test chat
# response = client.generate_response(
#     "Summarize the text: AI in healthcare.",
#     "AI is being used to improve diagnostics and treatment in healthcare."
# )
# print("Generated response:", response)
