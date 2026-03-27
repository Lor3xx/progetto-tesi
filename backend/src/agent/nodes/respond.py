import base64
import json
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document

from config import settings
from services.groq_client import llm
from agent.state import AgentState, ImageResult

# Prompt di sistema
RESPOND_SYSTEM_PROMPT = """
You are a specialized cybersecurity assistant. You answer questions based EXCLUSIVELY
on the provided document excerpts and images.

Rules:
- Answer only using the provided context. Never invent or assume information.
- Always cite your sources using the document name, without being redundant.
- If you use an image, explicitly mention it (e.g. "As shown in the diagram from doc.pdf, page 3"). Otherwise don't say that you didn't use one.
- If context is insufficient, say so clearly instead of guessing.
- Be precise, technical, and concise.
- Answer in the same language as the user's question.
"""

RESPOND_GENERIC_PROMPT = """
You are a specialized cybersecurity assistant answering a general cybersecurity question.
This is a foundational concept question, not requiring specific document lookup.
Be precise, technical, and educational. Mention that this is general knowledge,
not sourced from specific documents.
Answer in the same language as the user's question.
If the question is a greeting or a polite interaction respond in a friendly manner, 
without being too formal and say in what you can help.
Answer in the same language as the user's question.
"""


def _build_context_messages(state: AgentState) -> list:
    """
    Costruisce la lista di messaggi per il LLM combinando:
    - testo dei chunk recuperati
    - immagini originali in base64 con le loro descrizioni
    - domanda dell'utente
    """
    content = []

    # --- Chunk testuali ---
    if state["retrieved_chunks"]:
        chunks_text = "\n\n---\n\n".join([
            f"[Source: {c['document'].metadata.get('source', 'unknown')}, "
            f"page {c['document'].metadata.get('page', '?')}, "
            f"relevance: {c['score']:.2f}]\n"
            f"{c['document'].page_content}"
            for c in state["retrieved_chunks"]
        ])
        content.append({
            "type": "text",
            "text": f"DOCUMENT EXCERPTS:\n{chunks_text}"
        })

    # --- Chunk immagini: descrizione + immagine base64 ---
    for img_chunk in state["retrieved_image_chunks"]:
        img_path = img_chunk["document"].metadata.get("image_path", "")
        description = img_chunk["document"].page_content
        source = img_chunk["document"].metadata.get("source", "unknown")
        page = img_chunk["document"].metadata.get("page", "?")

        content.append({
            "type": "text",
            "text": (
                f"[IMAGE from {source}, page {page}, "
                f"relevance: {img_chunk['score']:.2f}]\n"
                f"Description: {description}"
            )
        })

        # Carica l'immagine reale in base64 solo se il file esiste
        img_file = Path(img_path)
        if img_file.exists():
            with open(img_file, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = img_file.suffix.lstrip(".")
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"}
            })

    # --- Domanda utente ---
    content.append({
        "type": "text",
        "text": (
            f"USER QUESTION: {state['user_query']}\n\n"
            "Answer based strictly on the context above. "
            "Cite sources explicitly. "
            "If you are using an image, say so."
        )
    })

    return content


def _extract_sources(state: AgentState) -> list[str]:
    """Raccoglie i nomi univoci dei documenti usati come fonti."""
    sources = set()
    for chunk in state["retrieved_chunks"]:
        sources.add(chunk["document"].metadata.get("source", "unknown"))
    for chunk in state["retrieved_image_chunks"]:
        sources.add(chunk["document"].metadata.get("source", "unknown"))
    return sorted(sources)


def _extract_images(state: AgentState) -> list[ImageResult]:
    """Costruisce la lista ImageResult per le immagini da mostrare al frontend."""
    images: list[ImageResult] = []
    for img_chunk in state["retrieved_image_chunks"]:
        meta = img_chunk["document"].metadata
        img_path = meta.get("image_path", "")
        if Path(img_path).exists():
            images.append(ImageResult(
                source=meta.get("source", "unknown"),
                image_path=img_path,
                page=meta.get("page", 0),
                description=img_chunk["document"].page_content,
            ))
    return images


def respond_node(state: AgentState) -> AgentState:
    """
    Nodo di risposta principale.
    Gestisce quattro casi:
    - off-topic: risponde che non può rispondere a domande fuori contesto
    - generic: risponde senza documenti
    - no_documents: comunica che non ci sono fonti pertinenti
    - rag: costruisce risposta da chunk testuali e immagini
    """

    # Caso 1: domanda off topic
    if state["is_off_topic"]:
        return {
            **state,
            "draft_response": (
                "I'm a specialized cybersecurity assistant and can only answer "
                "questions related to cybersecurity topics. "
                "Your question appears to be outside my area of expertise."
            ),
            "response_status": "off_topic",
            "sources": [],
            "images": [],
        }

    # Caso 2: domanda generica cybersecurity, nessun documento necessario
    if state["is_generic_cybersecurity"]:
        messages = [
            SystemMessage(content=RESPOND_GENERIC_PROMPT),
            HumanMessage(content=state["user_query"]),
        ]
        response = llm.invoke(messages)
        return {
            **state,
            "draft_response": response.content,
            "final_response": response.content,
            "response_status": "complete",
            "sources": [],
            "images": [],
        }

    # Caso 3: nessun chunk trovato sopra soglia
    has_chunks = (
        len(state["retrieved_chunks"]) > 0 or
        len(state["retrieved_image_chunks"]) > 0
    )
    if not has_chunks:
        return {
            **state,
            "draft_response": "",
            "final_response": (
                "I could not find any relevant documents to answer your question. "
                "Please make sure the topic is covered in the loaded knowledge base."
            ),
            "response_status": "unknown",
            "sources": [],
            "images": [],
        }

    # Caso 4: RAG normale con chunk e immagini
    content = _build_context_messages(state)
    messages = [
        SystemMessage(content=RESPOND_SYSTEM_PROMPT),
        HumanMessage(content=content),
    ]

    response = llm.invoke(messages)

    return {
        **state,
        "draft_response": response.content,
        "sources": _extract_sources(state),
        "images": _extract_images(state),
        # final_response resta vuoto finché evaluate non dà l'ok
        "final_response": "",
        "response_status": "unknown",
    }