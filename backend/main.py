from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.services.pdf_processor import ingest_base_knowledge

@asynccontextmanager
async def lifespan(app: FastAPI):
    # all'avvio: ingestisce i PDF base se non già presenti
    ingest_base_knowledge()
    yield

app = FastAPI(lifespan=lifespan)