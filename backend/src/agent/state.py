from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.documents import Document


class RetrievedChunk(TypedDict):
    """Rappresenta un chunk recuperato da ChromaDB con il suo score."""
    document: Document
    score: float


class ImageResult(TypedDict):
    """Immagine allegata alla risposta finale."""
    source: str        # nome del PDF di origine
    image_path: str    # path su disco per inviarla al frontend
    page: int          # pagina del documento
    description: str   # descrizione generata dal vision model


class AgentState(TypedDict):
    # --- Input iniziale ---
    user_query: str                          # domanda originale dell'utente

    # --- Classify ---
    is_generic_cybersecurity: bool          # True se domanda generica su cybersecurity
    is_off_topic: bool                     # True se domanda fuori contesto
    classify_reasoning: str                      # motivazione del classificatore

    # --- Query enhancement ---
    enhanced_query: str                      # query migliorata con keywords
    enhancement_reasoning: str              # perché è stata modificata così

    # --- Retrieval ---
    retrieved_chunks: list[RetrievedChunk]  # chunk testo + score
    retrieved_image_chunks: list[RetrievedChunk]  # chunk descrizioni immagini + score

    # --- Valutazione ---
    eval_score: float                        # score 0.0-1.0 della risposta bozza
    eval_reasoning: str                      # motivazione del valutatore
    missing_aspects: list[str]              # cosa manca per rispondere bene
    retry_count: int                         # quante volte ha già ripetuto il loop

    # --- Risposta ---
    draft_response: str                      # bozza generata prima della valutazione
    final_response: str                      # risposta finale approvata
    sources: list[str]                       # nomi dei documenti usati (citazioni)
    images: list[ImageResult]               # immagini da mostrare al frontend
    message_timestamp: list[str]
    
    # --- Flag di controllo del flusso ---
    query_category: str                         # "specific" | "generic_cyber" | "off_topic"
    response_status: str                    # "complete" | "partial" | "unknown"

    # --- Cronologia messaggi (LangChain messages) ---
    # add_messages è un reducer: invece di sovrascrivere, appende
    messages: Annotated[list, add_messages]