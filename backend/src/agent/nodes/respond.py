from pathlib import Path

from agent.prompts import RESPOND_GENERIC_PROMPT, RESPOND_SYSTEM_PROMPT, RESPOND_OFFTOPIC_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage

from services.llm_client import llm
from agent.state import AgentState, ImageResult

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

    # --- Chunk immagini: descrizione ---
    for img_chunk in state["retrieved_image_chunks"]:
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

    # --- Domanda utente ---
    content.append({
        "type": "text",
        "text": (
            f"USER QUESTION: {state['user_query']}\n\n"
            "Answer based strictly on the context above. "
        )
    })
    print("\nReturning content")
    return content


def _extract_sources(state: AgentState) -> list[dict]:
    """Estrae le fonti uniche dai chunk testuali per mostrarle al frontend."""
    print(f"\nExtracting sources from {len(state['retrieved_chunks'])} text chunks")
    seen = set()
    sources = []
    for chunk in state["retrieved_chunks"]:
        meta = chunk["document"].metadata
        source = meta.get("source", "unknown")
        page = meta.get("page", None)
        key = (source, page)
        if key not in seen:
            seen.add(key)
            sources.append({
                "metadata": {
                    "source": source,
                    "page": str(page) if page is not None else "",
                },
                "content": chunk["document"].page_content[:300],
            })
    print(f"Extracted sources: {[s['metadata'] for s in sources]}")
    return sources


def _extract_images(state: AgentState) -> list[ImageResult]:
    """Costruisce la lista ImageResult per le immagini da mostrare al frontend."""
    print(f"\nExtracting images from {len(state['retrieved_image_chunks'])} image chunks.")
    images: list[ImageResult] = []
    for img_chunk in state["retrieved_image_chunks"]:
        print(f"Extracting image from path {img_chunk['document'].metadata.get('image_path', '')}")
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

def extract_text_content(response):
    content = response.content

    # Se è già stringa (vecchio comportamento)
    if isinstance(content, str):
        return content

    # Se è lista (Gemini)
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "")

    return ""


def respond_node(state: AgentState) -> AgentState:
    """
    Nodo di risposta principale.
    Gestisce tre casi:
    - off-topic: risponde che non può rispondere a domande fuori contesto
    - generic: nessun documento trovato, risponde senza documenti
    - rag: costruisce risposta da chunk testuali e immagini
    """

    # Caso 1: domanda off topic
    if state["is_off_topic"] and not state["is_specific"]:
        messages = [
            SystemMessage(content=RESPOND_OFFTOPIC_PROMPT),
            *state["messages"],  # cronologia messaggi precedente
            HumanMessage(content=state["user_query"])
        ]
        response = llm.invoke(messages)
        raw_text = extract_text_content(response)
        return {
            **state,
            "draft_response": raw_text,
            "response_status": "complete",
            "sources": [],
            "images": [],
        }
    
    # Caso 2: nessun chunk trovato sopra soglia, domanda generica
    has_chunks = (
        len(state["retrieved_chunks"]) > 0 or
        len(state["retrieved_image_chunks"]) > 0
    )
    if not has_chunks:
        messages = [
            SystemMessage(content=RESPOND_GENERIC_PROMPT),
            *state["messages"],  # cronologia messaggi precedente
            HumanMessage(content=state["user_query"]),
        ]
        response = llm.invoke(messages)
        raw_text = extract_text_content(response)
        return {
            **state,
            "draft_response": raw_text,
            "final_response": raw_text,
            "response_status": "complete",
            "is_generic_cybersecurity": True,
            "sources": [],
            "images": [],
        }

    # Caso 3: RAG normale con chunk e immagini
    content = _build_context_messages(state)
    messages = [
        SystemMessage(content=RESPOND_SYSTEM_PROMPT),
        *state["messages"],  # cronologia messaggi precedente
        HumanMessage(content=content),
    ]
    print(f"\nInvoking LLM with {len(messages)} messages, including {len(state['retrieved_chunks'])} text chunks and {len(state['retrieved_image_chunks'])} image chunks.")
    response = llm.invoke(messages)
    raw_text = extract_text_content(response)
    print("\nReturning response")

    return {
        **state,
        "draft_response": raw_text,
        "sources": _extract_sources(state),
        "images": _extract_images(state),
        "is_generic_cybersecurity": False,
        "is_off_topic": False,
        "is_specific": True,
        # final_response resta vuoto finché evaluate non da l'ok
        "final_response": "",
        "response_status": "unknown",
    }