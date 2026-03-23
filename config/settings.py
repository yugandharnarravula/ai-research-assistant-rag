import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "docs")
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    DEFAULT_K = int(os.getenv("DEFAULT_K", 5))
    FINAL_TOP_K = 3  # after reranking
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    STREAMLIT_BACKEND_URL = os.getenv("STREAMLIT_BACKEND_URL", "http://localhost:8000")


settings = Settings()
