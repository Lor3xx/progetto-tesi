from pydantic_settings import BaseSettings
import os
import dotenv

dotenv.load_dotenv()

class Settings(BaseSettings):
    # Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    groq_llm_model: str = "llama-3.3-70b-versatile"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    
    # HuggingFace Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # ChromaDB
    chroma_path: str = "./data/chroma_db"
    chroma_collection: str = "cybersecurity_docs"
    
    # Chunking
    chunk_size: int = 512
    chunk_overlap: int = 64
    
    # Logica agente
    retrieval_top_k: int = 5
    min_eval_score: float = 0.7
    max_retries: int = 2

    # Accettazione nuovi documenti
    min_acceptable_score: float = 0.6 #se inferiore rifiuto
    min_ingestion_score: float = 0.8 #se maggiore accetto, se in mezzo chiedo a llm


settings = Settings()  # istanza globale, importi questa ovunque