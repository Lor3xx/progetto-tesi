from langchain_community.vectorstores import Chroma
from config import settings
from services.groq_client import embeddings

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


def similarity_search(query: str, k: int | None = None) -> list:
    """
    Cerca i documenti più simili alla query.
    Restituisce una lista di Document con score di rilevanza.
    """
    top_k = k or settings.retrieval_top_k
    results = vector_store.similarity_search_with_relevance_scores(query, k=top_k)
    # results è una lista di tuple (Document, score)
    return results


def document_exists(source: str) -> bool:
    """
    Controlla se un documento con questo nome file è già nel DB,
    per evitare duplicati al momento del caricamento.
    """
    result = vector_store.get(where={"source": source})
    return len(result["ids"]) > 0