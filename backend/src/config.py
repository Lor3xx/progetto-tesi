from pydantic_settings import BaseSettings
import os
import dotenv
from pathlib import Path

dotenv.load_dotenv()

class Settings(BaseSettings):
    # Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY")
    groq_eval_model: str = "llama-3.1-8b-instant"  # veloce e leggero
    groq_llm_model: str = "llama-3.3-70b-versatile"  # solo per risposta finale
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
    retrieval_top_k: int = 8
    user_boost: float = 0.15 # bonus score per i documenti caricati dall'utente
    min_eval_chunk_score: float = 0.5 #soglia per considerare un chunk rilevante e usarlo nella risposta
    min_eval_score: float = 0.7 #soglia minima per accettare la risposta del modello senza retry
    max_retries: int = 2

    # Accettazione nuovi documenti
    uploads_dir: Path = Path("./data/uploads")
    max_file_size: int = 50 * 1024 * 1024  # 50 MB
    sample_pages_for_validation: int = 5
    min_chars_for_validation: int = 200
    min_acceptable_score: float = 0.3 #se inferiore rifiuto
    min_ingestion_score: float = 0.8 #se maggiore accetto, se in mezzo chiedo a llm

    # Checkpointing con SQLite
    sqlite_path: str = "./data/chat_history.db"


settings = Settings()  # istanza globale, importi questa ovunque