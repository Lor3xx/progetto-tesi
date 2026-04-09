import json
from agent.prompts import RERANK_PROMPT
from agent.state import AgentState
from services.llm_client import llm

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


def rerank_node(state: AgentState) -> dict:
    chunks = state.get("retrieved_chunks", [])
    image_chunks = state.get("retrieved_image_chunks", [])
    query = state.get("enhanced_query") or state["messages"][-1].content

    result = {}

    # --- rerank chunk testuali ---
    if len(chunks) > 1:
        numbered = "\n\n".join([
            f"[{i}]\n{chunk['document'].page_content[:600]}"
            for i, chunk in enumerate(chunks)
        ])
        prompt = RERANK_PROMPT.format(
            query=query,
            n=len(chunks),
            chunks=numbered,
        )
        try:
            print("\nInvoking rerank_node for text chunks")
            response = llm.invoke(prompt)
            raw_text = extract_text_content(response)
            raw = raw_text.strip()
            # rimuove eventuali backtick markdown
            raw = raw.replace("```json", "").replace("```", "").strip()
            indices = json.loads(raw)
            print(f"Reranking result: {indices}")
            # valida che gli indici siano sensati prima di usarli
            if (
                isinstance(indices, list)
                and len(indices) == len(chunks)
                and set(indices) == set(range(len(chunks)))
            ):
                result["retrieved_chunks"] = [chunks[i] for i in indices]
        except Exception:
            print("Reranking failed, keeping original order of chunks.")
            pass  # se fallisce mantieni l'ordine originale

    # --- rerank immagini ---
    if len(image_chunks) > 1:
        numbered = "\n\n".join([
            f"[{i}]\n{img['document'].page_content[:400]}"
            for i, img in enumerate(image_chunks)
        ])
        prompt = RERANK_PROMPT.format(
            query=query,
            n=len(image_chunks),
            chunks=numbered,
        )
        try:
            print("\nInvoking rerank_node for image chunks")
            response = llm.invoke(prompt)
            raw_text = extract_text_content(response)
            raw = raw_text.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            indices = json.loads(raw)
            print(f"Reranking result for images: {indices}")
            if (
                isinstance(indices, list)
                and len(indices) == len(image_chunks)
                and set(indices) == set(range(len(image_chunks)))
            ):
                result["retrieved_image_chunks"] = [image_chunks[i] for i in indices]
        except Exception:
            print("Reranking failed, keeping original order of image chunks.")
            pass

    return {
        **state,
        "retrieved_chunks": result.get("retrieved_chunks", chunks),
        "retrieved_image_chunks": result.get("retrieved_image_chunks", image_chunks),
    }