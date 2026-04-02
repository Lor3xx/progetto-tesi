from uuid import uuid4
import sqlite3

from fastapi import APIRouter, HTTPException, Request
from api.schemas import ChatRequest, ChatResponse, ImageResult
from agent.state import AgentState
from config import settings

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    rag_graph = req.app.state.rag_graph  # recuperato da app.state

    if not rag_graph:
        raise HTTPException(status_code=503, detail="Sistema non ancora pronto")

    thread_id = request.thread_id or str(uuid4())

    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.execute(
        "INSERT OR IGNORE INTO conversations (thread_id, title) VALUES (?, ?)",
        (thread_id, request.message[:80])
    )
    conn.commit()

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
    )

    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = rag_graph.invoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore nel grafo: {str(e)}")

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


@router.get("/history/{thread_id}")
async def get_history(thread_id: str, req: Request):
    rag_graph = req.app.state.rag_graph

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
            "sources": msg.metadata.get("sources", []) if hasattr(msg, "metadata") else [],
            "images": msg.metadata.get("images", []) if hasattr(msg, "metadata") else [],
            "timestamp": msg.metadata.get("timestamp", "") if hasattr(msg, "metadata") else "",
        }
        for msg in messages
    ]

    return {"thread_id": thread_id, "messages": history}