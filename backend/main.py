import sys
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager
from uuid import uuid4

from api.schemas import ChatRequest, ChatResponse, ImageResult
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.append(str(Path(__file__).parent / "src"))

from config import settings
from agent.graph import build_graph
from langgraph.checkpoint.sqlite import SqliteSaver

from src.api.conversations import router as conversations_router


# ─── Global state ─────────────────────────────────────────────────────────────

rag_graph = None


# ─── Startup / Shutdown ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_graph

    print("Inizializzazione RAG system...")

    # Checkpointer SQLite per la persistenza delle conversazioni
    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")

    # ✅ crea tabella conversations se non esiste
    conn.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        thread_id TEXT PRIMARY KEY,
        title TEXT
    )
    """)
    conn.commit()

    checkpointer = SqliteSaver(conn)
    rag_graph = build_graph(checkpointer=checkpointer)

    print("Backend pronto.")
    yield

    # Shutdown — chiude la connessione SQLite
    conn.close()


# ─── FastAPI app ──────────────────────────────────────────────────────────────

app = FastAPI(title="RAG Cybersecurity API", version="1.0.0", lifespan=lifespan)

app.include_router(conversations_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve le immagini estratte dai PDF direttamente al frontend
images_dir = Path("data/images")
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ready" if rag_graph else "initializing"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not rag_graph:
        raise HTTPException(status_code=503, detail="Sistema non ancora pronto")

    thread_id = request.thread_id or str(uuid4())

    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.execute(
        "INSERT OR IGNORE INTO conversations (thread_id, title) VALUES (?, ?)",
        (thread_id, request.message[:80])
    )
    conn.commit()

    from agent.state import AgentState
    initial_state = AgentState(
        user_query=request.message,
        enhanced_query="",
        enhancement_reasoning="",
        retrieved_chunks=[],
        retrieved_image_chunks=[],
        eval_score=0.0,
        eval_reasoning="",
        missing_aspects=[],
        retry_count=0,
        draft_response="",
        final_response="",
        sources=[],
        images=[],
        is_generic_cybersecurity=False,
        is_off_topic=False,
        query_category="unknown",
        response_status="unknown",
        messages=[],
    )

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = rag_graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel grafo: {str(e)}")

    #print di debug
    print(f"Status        : {result['response_status']}")
    print(f"Is generic    : {result['is_generic_cybersecurity']}")
    print(f"Is off-topic  : {result['is_off_topic']}")
    print(f"Enhanced query: {result['enhanced_query']}")
    print(f"Eval score    : {result['eval_score']:.2f}")
    print(f"Retry count   : {result['retry_count']}")
    print(f"Sources       : {result['sources']}")
    print(f"Images found  : {len(result['images'])}")

    return ChatResponse(
        answer=result["final_response"],
        thread_id=thread_id,
        sources=result["sources"],
        images=[ImageResult(**img) for img in result["images"]],
        status=result["response_status"],
        is_generic=result["is_generic_cybersecurity"],
        is_off_topic=result["is_off_topic"],
        query_category=result["query_category"],
    )


@app.get("/chat/history/{thread_id}")
async def get_history(thread_id: str):
    if not rag_graph:
        raise HTTPException(status_code=503, detail="Sistema non ancora pronto")

    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = rag_graph.get_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Conversazione non trovata")

    messages = state.values.get("messages", [])
    history = [
        {
            "role": "user" if msg.__class__.__name__ == "HumanMessage" else "assistant",
            "content": msg.content,
        }
        for msg in messages
    ]

    return {"thread_id": thread_id, "messages": history}


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)