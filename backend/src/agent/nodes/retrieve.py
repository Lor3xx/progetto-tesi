from config import settings
from services.chroma_service import similarity_search_prioritized
from agent.state import AgentState, RetrievedChunk

def retrieve_node(state: AgentState) -> AgentState:
    query = state["enhanced_query"]
    results = similarity_search_prioritized(query, k=settings.retrieval_top_k)

    text_chunks: list[RetrievedChunk] = []
    image_chunks: list[RetrievedChunk] = []

    for doc, score in results:
        # Filtra subito i chunk sotto soglia
        if score < settings.min_eval_chunk_score:
            continue

        chunk: RetrievedChunk = {"document": doc, "score": score}
        if doc.metadata.get("chunk_type") == "image_description":
            image_chunks.append(chunk)
        else:
            text_chunks.append(chunk)

    return {
        **state,
        "retrieved_chunks": text_chunks,
        "retrieved_image_chunks": image_chunks,
        "retry_count": state["retry_count"] + 1,
    }