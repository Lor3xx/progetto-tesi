import re
import hashlib
from pathlib import Path
from datetime import datetime

import pymupdf
import pymupdf4llm
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from services.groq_client import describe_image
from config import settings
from services.chroma_service import add_documents, document_exists

from services.image_extractor import extract_images_from_pdf, save_image_registry

IMAGES_DIR = Path("data/images")


# --- Splitter condiviso ---
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def _extract_text(pdf_path: Path) -> str:
    """
    Usa pymupdf4llm per estrarre il testo dal PDF in formato Markdown.
    - header=False / footer=False: rimuove loghi, titoli ripetuti e numeri di pagina.
    - ignore_images=True: non include le immagini nel testo estratto
      (le immagini non portano testo utile per l'embedding).
    - OCR automatico sulle pagine che non contengono testo selezionabile.
    """
    doc = pymupdf.open(str(pdf_path))
    md_text = pymupdf4llm.to_markdown(
        doc,
        header=False,        # rimuove header ripetuti (loghi, titolo doc)
        footer=False,        # rimuove footer (numeri pagina, copyright)
        ignore_images=True,  # le immagini non vengono convertite in testo
        show_progress=False,
    )
    doc.close()
    return md_text


def _clean_text(text: str) -> str:
    """
    Pulizia aggiuntiva del testo estratto:
    - rimuove righe che contengono solo simboli o numeri isolati (residui di tabelle grafiche)
    - comprime spazi bianchi eccessivi
    - rimuove separatori markdown inutili
    """
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # scarta righe vuote o composte solo da simboli/trattini (es. "---", "===", "...")
        if not stripped:
            continue
        if re.fullmatch(r"[-=_|*#~\s]+", stripped):
            continue
        # scarta righe che sono solo un numero (numero pagina residuo)
        if re.fullmatch(r"\d{1,4}", stripped):
            continue
        cleaned.append(stripped)

    return "\n".join(cleaned)


def _make_chunk_id(source: str, chunk_index: int, text: str) -> str:
    """
    Genera un ID deterministico per ogni chunk basato su fonte + indice + hash del testo.
    Questo permette di evitare duplicati se il file viene ricaricato.
    """
    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    return f"{source}::chunk_{chunk_index:04d}::{content_hash}"


def process_and_ingest_pdf(
    pdf_path: Path,
    uploaded_by: str = "system",
    overwrite: bool = False,
) -> dict:
    """
    Pipeline completa: estrai → pulisci → splitta → embedda → salva in ChromaDB.

    Args:
        pdf_path:     percorso al file PDF
        uploaded_by:  'system' per i PDF in base_knowledge, 'user' per upload utente
        overwrite:    se True reingestisce anche se già presente nel DB

    Returns:
        dizionario con statistiche dell'ingestion
    """
    source = pdf_path.name

    # evita duplicati
    if not overwrite and document_exists(source):
        return {"status": "skipped", "source": source, "reason": "already_exists"}

    # 1. Estrazione testo
    raw_text = _extract_text(pdf_path)

    # 2. Pulizia
    clean = _clean_text(raw_text)

    if len(clean.strip()) < 50:
        return {"status": "error", "source": source, "reason": "empty_after_extraction"}

    # 3. Splitting in chunk
    chunks = _splitter.split_text(clean)

    # 4. Costruzione LangChain Documents con metadata
    total_pages = pymupdf.open(str(pdf_path)).page_count
    chars_per_page = max(1, len(clean) // total_pages)

    documents = []
    chunk_meta_for_manifest = []

    for i, chunk_text in enumerate(chunks):
        # stima della pagina in base alla posizione del chunk nel testo
        char_offset = len("\n".join(chunks[:i]))
        estimated_page = min(total_pages, (char_offset // chars_per_page) + 1)

        chunk_id = _make_chunk_id(source, i, chunk_text)
        metadata = {
            "source": source,
            "chunk_id": chunk_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "page": estimated_page,
            "uploaded_by": uploaded_by,
            "ingested_at": datetime.now().isoformat(),
        }
        documents.append(Document(page_content=chunk_text, metadata=metadata))
        chunk_meta_for_manifest.append(metadata)

    # 5. Embedding + salvataggio in ChromaDB
    ids = add_documents(documents)

    # Estrai immagini e salva manifest
    page_images = extract_images_from_pdf(pdf_path, IMAGES_DIR)
    image_records = []

    for page_num, img_paths in page_images.items():
        # Recupera il testo dei chunk sulla stessa pagina come contesto
        page_chunks_text = " ".join([
            doc.page_content
            for doc in documents
            if doc.metadata.get("page") == page_num
        ])

        for img_path in img_paths:
            description = describe_image(Path(img_path), context=page_chunks_text)

            # Il modello vision dice SKIP se l'immagine non ha info utili
            if description.upper().startswith("SKIP"):
                image_records.append({
                    "path": img_path, "page": page_num, "status": "skipped"
                })
                continue

            # Costruisce un Document LangChain dalla descrizione dell'immagine.
            # È identico ai chunk testuali: viene embeddato e cercato allo stesso modo.
            # Il metadata 'image_path' permette al RAG di sapere
            # che questo chunk ha un'immagine allegata da mostrare.
            image_doc = Document(
                page_content=description,
                metadata={
                    "source": source,
                    "chunk_id": _make_chunk_id(source + "_img", page_num, description),
                    "chunk_type": "image_description",   # distingue dai chunk testuali
                    "image_path": img_path,              # path per mostrare l'immagine
                    "page": page_num,
                    "uploaded_by": uploaded_by,
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )
            add_documents([image_doc])
            image_records.append({
                "path": img_path, "page": page_num,
                "status": "embedded", "chunk_id": image_doc.metadata["chunk_id"]
            })

    save_image_registry(pdf_path, image_records, IMAGES_DIR)

    return {
        "status": "success",
        "source": source,
        "chunks_ingested": len(ids),
        "uploaded_by": uploaded_by,
    }


def ingest_base_knowledge(base_dir: Path | None = None) -> list[dict]:
    """
    Scansiona la cartella data/base_knowledge e ingestisce tutti i PDF trovati.
    Da chiamare allo startup del server (in main.py con lifespan).
    """
    folder = base_dir or Path("data/base_knowledge")
    results = []
    for pdf_file in sorted(folder.glob("*.pdf")):
        result = process_and_ingest_pdf(pdf_file, uploaded_by="system")
        results.append(result)
        print(f"[ingest] {pdf_file.name}: {result['status']}")
    return results