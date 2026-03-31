from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ImageResult(BaseModel):
    source: str
    image_path: str
    page: int
    description: str

class SourceDocument(BaseModel):
    content: str
    metadata: dict[str, str]


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    sources: list[SourceDocument]
    images: list[ImageResult]
    status: str
    is_generic: bool
    is_off_topic: bool
    query_category: str


class HistoryMessage(BaseModel):
    role: str
    content: str


class ConversationPreview(BaseModel):
    thread_id: str
    title: str          # primo messaggio utente oppure fallback "Conversazione"
    created_at: str     # ISO-8601 UTC
    updated_at: str     # ISO-8601 UTC (checkpoint più recente)
    message_count: int  # numero approssimativo di turni utente


class ConversationListResponse(BaseModel):
    conversations: list[ConversationPreview]
    total: int

class TitleUpdate(BaseModel):
    new_title: str

class UploadResponse(BaseModel):
    filename:   str
    saved_as:   str | None   # None se rifiutato prima del salvataggio
    size_bytes: int
    status:     str          # uploaded | duplicate | rejected | error
    message:    str
    # campi extra solo in caso di successo
    chunks_ingested: int | None = None
    validation_score: float | None = None
    validation_method: str | None = None