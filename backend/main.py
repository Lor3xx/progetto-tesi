import sys
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

sys.path.append(str(Path(__file__).parent / "src"))

from src.config import settings
from src.agent.graph import build_graph
from langgraph.checkpoint.sqlite import SqliteSaver

from src.api.chat import router as chat_router
from src.api.conversations import router as conversations_router
from src.api.documents import router as documents_router

# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Inizializzazione RAG system...")

    # Checkpointer SQLite per la persistenza delle conversazioni
    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # crea tabella conversations se non esiste
    conn.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        thread_id TEXT PRIMARY KEY,
        title TEXT,
        settings TEXT DEFAULT '{"tone": "technical", "temperature": 0.2, "response_length": "balanced"}'
    )
    """)
    conn.commit()

    checkpointer = SqliteSaver(conn)
    rag_graph = build_graph(checkpointer=checkpointer)
    app.state.rag_graph = rag_graph  # salva su app.state invece che globale

    print("Backend pronto.")
    yield

    # Shutdown — chiude la connessione SQLite
    conn.close()


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="RAG Cybersecurity API", version="1.0.0", lifespan=lifespan)

app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(documents_router)

# Serve le immagini estratte dai PDF direttamente al frontend
app.mount("/images", StaticFiles(directory="data/images"), name="images")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ready" if app.state.rag_graph else "initializing"}

# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)