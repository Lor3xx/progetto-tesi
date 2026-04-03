import hashlib
from pathlib import Path

 
from api.schemas import UploadResponse
from fastapi import APIRouter, HTTPException, UploadFile, File
 
from services.document_validator import validate_document
from services.pdf_processor import process_and_ingest_pdf

from config import settings

ALLOWED_CONTENT_TYPES = {"application/pdf"}

router = APIRouter(prefix="/documents", tags=["documents"])

def _safe_stem(name: str) -> str:
    stem = Path(name).stem
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in stem)
    return (safe[:100] or "document")

# ── Endpoints ─────────────────────────────────────────────────────────────────
 
@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
 
    # 1. Content-type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Solo file PDF sono supportati.")
 
    # 2. Leggi + size check
    data = await file.read()
    if len(data) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande. Massimo: {settings.max_file_size // (1024*1024)} MB.",
        )
 
    # 3. Magic bytes
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="Il file non è un PDF valido.")
 
    # 4. Deduplicazione per hash contenuto
    content_hash = hashlib.sha256(data).hexdigest()[:16]
    stem         = _safe_stem(file.filename or "document")
    dest_path    = settings.uploads_dir / f"{stem}_{content_hash}.pdf"
    original_name = file.filename or "document.pdf"
 
    if dest_path.exists():
        return UploadResponse(
            filename=original_name,
            saved_as=dest_path.name,
            size_bytes=len(data),
            status="duplicate",
            message="Documento già presente, non è stato ricaricato.",
        )
 
    # 5. Salva temporaneamente su disco (serve per pymupdf)
    dest_path.write_bytes(data)
 
    # 6. Validazione cybersecurity
    try:
        validation = validate_document(dest_path)
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante la validazione del documento: {exc}",
        )
 
    if not validation.accepted:
        # Rimuovi il file — non verrà indicizzato
        dest_path.unlink(missing_ok=True)
        return UploadResponse(
            filename=original_name,
            saved_as=None,
            size_bytes=len(data),
            status="rejected",
            message=f"Documento rifiutato: {validation.reason}",
            validation_score=round(validation.score, 3),
            validation_method=validation.method,
        )
 
    # 7. Ingestion in ChromaDB
    try:
        result = process_and_ingest_pdf(dest_path, uploaded_by="user")
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'indicizzazione: {exc}",
        )
 
    if result["status"] == "error":
        dest_path.unlink(missing_ok=True)
        return UploadResponse(
            filename=original_name,
            saved_as=None,
            size_bytes=len(data),
            status="error",
            message=f"Errore estrazione testo: {result.get('reason', 'unknown')}",
        )
 
    return UploadResponse(
        filename=original_name,
        saved_as=dest_path.name,
        size_bytes=len(data),
        status="uploaded",
        message="Documento caricato e indicizzato con successo.",
        chunks_ingested=result.get("chunks_ingested"),
        validation_score=round(validation.score, 3),
        validation_method=validation.method,
    )
 
 
@router.get("/list")
async def list_documents():
    files = sorted(
        settings.uploads_dir.glob("*.pdf"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return {
        "documents": [
            {"filename": p.name, "size_bytes": p.stat().st_size}
            for p in files
        ]
    }