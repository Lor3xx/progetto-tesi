from langchain_chroma import Chroma
from config import settings
from services.groq_client import embeddings, hyde_embedder

vector_store = Chroma(
    collection_name=settings.chroma_collection,
    embedding_function=embeddings,
    persist_directory=settings.chroma_path,
)


def get_vector_store() -> Chroma:
    """Restituisce l'istanza del vector store. Usata come dipendenza."""
    return vector_store


def add_documents(docs: list) -> list[str]:
    """
    Aggiunge una lista di LangChain Document al vector store.
    Restituisce gli ID assegnati ai chunk.
    """
    ids = vector_store.add_documents(docs)
    return ids

def _clamp_scores(results: list[tuple]) -> list[tuple]:
    """Garantisce che gli score siano sempre in [0, 1] indipendentemente
    da eventuali imprecisioni numeriche del modello di embedding."""
    return [(doc, max(0.0, min(score, 1.0))) for doc, score in results]

# Legacy
def similarity_search(query: str, k: int | None = None) -> list:
    """
    Cerca i documenti più simili alla query tra quelli della knowledge base.
    Restituisce una lista di Document con score di rilevanza.
    """
    top_k = k or settings.retrieval_top_k
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    # results è una lista di tuple (Document, score)
    return _clamp_scores(results)


def document_exists(source: str) -> bool:
    """
    Controlla se un documento con questo nome file è già nel DB,
    per evitare duplicati al momento del caricamento.
    """
    result = vector_store.get(where={"source": source})
    return len(result["ids"]) > 0


def similarity_search_prioritized(query: str, k: int | None = None) -> list:
    """
    Ricerca su tutta la collection con boost per i documenti utente.
    Recupera più risultati del necessario, applica il boost, riordina e taglia a k.
    """
    top_k = k or settings.retrieval_top_k

    hyde_embedding = hyde_embedder.embed_query(query)

    # Recupera più risultati del necessario per avere margine dopo il riordino
    candidates = vector_store.similarity_search_by_vector_with_relevance_scores(
        hyde_embedding,
        k=top_k * 3,
    )

    candidates = _clamp_scores(candidates)

    # Applica boost ai documenti utente
    boosted = []
    for doc, score in candidates:
        if doc.metadata.get("uploaded_by") == "user":
            boosted.append((doc, min(score + settings.user_boost, 1.0)))
        else:
            boosted.append((doc, score))

    # Riordina per score decrescente e taglia a k
    boosted.sort(key=lambda x: x[1], reverse=True)
    return boosted[:top_k]

def similarity_search_images(query: str, k: int = 3) -> list:
    """Cerca specificamente tra i chunk image_description."""

    hyde_embedding = hyde_embedder.embed_query(query)
    
    results = vector_store.similarity_search_by_vector_with_relevance_scores(
        hyde_embedding,
        k=k,
        filter={"chunk_type": "image_description"},
    )

    results = _clamp_scores(results)
    # Riordina per score decrescente
    results.sort(key=lambda x: x[1], reverse=True)

    return results