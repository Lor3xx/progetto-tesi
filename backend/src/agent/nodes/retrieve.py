from config import settings
from services.chroma_service import similarity_search_images, similarity_search_prioritized
from agent.state import AgentState, RetrievedChunk

def retrieve_node(state: AgentState) -> AgentState:
    query = state["enhanced_query"]
    results = similarity_search_prioritized(query, k=settings.retrieval_top_k)
    image_results = similarity_search_images(query, k=3)
    
    text_chunks: list[RetrievedChunk] = []
    image_chunks: list[RetrievedChunk] = []

    doc_sources = set()

    for doc, score in results:
        # Filtra subito i chunk sotto soglia
        if score < settings.min_eval_chunk_score:
            continue

        chunk: RetrievedChunk = {"document": doc, "score": score}
        
        text_chunks.append(chunk)
        doc_sources.add(doc.metadata.get("source", "unknown"))

    # Aggiunge immagini dalla ricerca dedicata con soglia più permissiva
    existing_ids = {c["document"].metadata.get("chunk_id") for c in image_chunks}
    for doc, score in image_results:
        chunk_id = doc.metadata.get("chunk_id")
        image_source = doc.metadata.get("source", "unknown")
        if score >= settings.min_image_score and chunk_id not in existing_ids and image_source in doc_sources:  # soglia bassa per immagini
            image_chunks.append({"document": doc, "score": score})
            existing_ids.add(chunk_id)
            
    return {
        **state,
        "retrieved_chunks": text_chunks,
        "retrieved_image_chunks": image_chunks,
        "retry_count": state["retry_count"] + 1,
    }