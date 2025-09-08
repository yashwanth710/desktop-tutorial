# import os
# from dotenv import load_dotenv

# load_dotenv()

# class Settings:
#     # Azure OpenAI
#     AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
#     AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
#     AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
#     AZURE_EMBEDDING_DEPLOYMENT = os.getenv('AZURE_EMBEDDING_DEPLOYMENT', 'text-embedding-3-large')
#     AZURE_LLM_DEPLOYMENT = os.getenv('AZURE_LLM_DEPLOYMENT', 'gpt-4.1-2025-04-14')
#     AZURE_VISION_DEPLOYMENT = os.getenv('AZURE_VISION_DEPLOYMENT', 'gpt-4o-2024-08-06')
    
#     # Qdrant
#     QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
#     QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
    
#     # OCR
#     TESSERACT_PATH = os.getenv('TESSERACT_PATH', '/usr/bin/tesseract')
    
#     # App settings
#     CHUNK_SIZE = 200
#     SEARCH_LIMIT = 5
#     MAX_HISTORY_MESSAGES = 5

# settings = Settings()

class Settings:
    # Azure OpenAI REST URLs
    AZURE_OPENAI_API_KEY = "5Xz4qzHJIM5gveRUM9pr30iHKWxkT1gw4l0HORcKSTzzjObbnMqNJQQJ99BFACHYHv6XJ3w3AAABACOGxLfq"
    
    # Chat/completion endpoints
    DEPLOYMENT_URL_CHAT_GPT4_1 = "https://rmes-openai-services.openai.azure.com/openai/deployments/gpt-4.1/chat/completions?api-version=2025-01-01-preview"
    DEPLOYMENT_URL_CHAT_GPT4_1_MINI = "https://rmes-openai-services.openai.azure.com/openai/deployments/gpt-4.1-mini/chat/completions?api-version=2025-01-01-preview"
    DEPLOYMENT_URL_CHAT_GPT4O = "https://rmes-openai-services.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2025-01-01-preview"
    
    # Embedding endpoint
    DEPLOYMENT_URL_EMBEDDING = "https://rmes-openai-services.openai.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15"

    # Qdrant
    QDRANT_URL = "http://localhost:6333"
    QDRANT_API_KEY = None  # Replace if you have one
    
    # OCR (Tesseract)
    # TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update for Windows or Linux path
    
    # App settings
    CHUNK_SIZE = 200
    SEARCH_LIMIT = 5
    MAX_HISTORY_MESSAGES = 5


settings = Settings()
