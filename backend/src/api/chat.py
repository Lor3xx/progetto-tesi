from uuid import uuid4
import sqlite3

from fastapi import APIRouter, HTTPException, Request
from api.schemas import ChatRequest, ChatResponse, ImageResult
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from config import settings
from services.llm_client import llm_eval

router = APIRouter(prefix="/chat", tags=["chat"])

def generate_title(user_message: str) -> str:
    messages = [
        SystemMessage(content=(
            "Generate a short, concise title (max 6 words) for a conversation "
            "based on the user's first message. No punctuation, no quotes."
            "Write the title in the same language as the message."
        )),
        HumanMessage(content=user_message)
    ]

    response = llm_eval.invoke(messages)
    print(f"Generated title: {response}")

    return response.content.strip()


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    print(f"*" * 50)
    print(f"*" * 50)
    print(f"Received query: {request.message[:100]}")
    rag_graph = req.app.state.rag_graph  # recuperato da app.state

    if not rag_graph:
        raise HTTPException(status_code=503, detail="Sistema non ancora pronto")

    thread_id = request.thread_id or str(uuid4())
    is_new_conversation = request.thread_id is None

    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)

    if is_new_conversation:
        try:
            title = generate_title(request.message)
        except Exception:
            title = request.message[:80]  # fallback
    else:
        title = None

    conn.execute(
        "INSERT OR IGNORE INTO conversations (thread_id, title) VALUES (?, ?)",
        (thread_id, title)
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
        print(f"❌ Errore durante l'invocazione del grafo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore nel grafo: {str(e)}")

    #print di debug
    print(f"=" * 50)
    print(f"Status        : {result['response_status']}")
    print(f"Is generic    : {result['is_generic_cybersecurity']}")
    print(f"Is off-topic  : {result['is_off_topic']}")
    print(f"Classify reasoning: {result['classify_reasoning']}")
    print(f"Enhanced query: {result['enhanced_query']}")
    print(f"Enhancement reasoning: {result['enhancement_reasoning']}")
    print(f"Eval score    : {result['eval_score']:.2f}")
    print(f"Eval reasoning: {result['eval_reasoning']}")
    print(f"Retry count   : {result['retry_count']}")
    print(f"Retrieved chunk scores: {[chunk['score'] for chunk in result['retrieved_chunks']]}")
    print(f"Retrieved image chunks scores: {[chunk['score'] for chunk in result['retrieved_image_chunks']]}")
    print(f"Sources       : {len(result['sources'])}")
    print(f"Images found  : {len(result['images'])}")
    print(f"Draft response : {result['draft_response'][:500]}...")
    print(f"=" * 50)

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