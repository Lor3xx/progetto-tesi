from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None


class ImageResult(BaseModel):
    source: str
    image_path: str
    page: int
    description: str


class ChatResponse(BaseModel):
    answer: str
    thread_id: str
    sources: list[str]
    images: list[ImageResult]
    status: str
    is_generic: bool


class HistoryMessage(BaseModel):
    role: str
    content: str