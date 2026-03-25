import json
import hashlib
import io
from pathlib import Path

import pymupdf
from PIL import Image

# Dimensione minima per considerare un'immagine utile (filtra loghi piccoli)
MIN_WIDTH = 100
MIN_HEIGHT = 100
# Soglia per scartare immagini quasi completamente bianche (sfondi, separatori)
WHITE_RATIO_THRESHOLD = 0.95


def _is_useful_image(image_bytes: bytes, width: int, height: int) -> bool:
    """
    Filtra immagini inutili:
    - troppo piccole (loghi, icone, decorazioni)
    - quasi completamente bianche (sfondi, spazi vuoti)
    """
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return False

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        histogram = img.histogram()
        white_pixels = histogram[255]
        total_pixels = sum(histogram)
        if white_pixels / total_pixels >= WHITE_RATIO_THRESHOLD:
            return False
    except Exception:
        return False

    return True


def _image_hash(image_bytes: bytes) -> str:
    """Hash MD5 dei byte dell'immagine, usato per evitare duplicati."""
    return hashlib.md5(image_bytes).hexdigest()[:10]


def extract_images_from_pdf(
    pdf_path: Path,
    images_base_dir: Path,
) -> dict[int, list[str]]:
    """
    Estrae le immagini utili dal PDF e le salva su disco.

    Restituisce un dizionario:
        { numero_pagina: [path_immagine_1, path_immagine_2, ...] }

    Questo dict viene usato da pdf_processor per collegare le immagini ai chunk.
    """
    doc_name = pdf_path.stem  # nome file senza estensione
    output_dir = images_base_dir / doc_name
    output_dir.mkdir(parents=True, exist_ok=True)

    doc = pymupdf.open(str(pdf_path))
    # page_number (1-based) → lista di path immagini salvate
    page_images: dict[int, list[str]] = {}
    seen_hashes: set[str] = set()  # evita di salvare la stessa immagine due volte

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_num = page_index + 1  # 1-based, più leggibile nei metadata
        image_list = page.get_images(full=True)

        for img_tuple in image_list:
            xref = img_tuple[0]
            smask = img_tuple[1]  # canale alpha/trasparenza

            try:
                image_dict = doc.extract_image(xref)
                image_bytes = image_dict["image"]
                ext = image_dict["ext"]
                width = image_dict["width"]
                height = image_dict["height"]

                # Gestione trasparenza: unisce il canale alpha se presente
                # (senza questo le immagini PNG con trasparenza risultano distorte)
                if smask != 0:
                    pix_base = pymupdf.Pixmap(image_bytes)
                    pix_mask = pymupdf.Pixmap(doc.extract_image(smask)["image"])
                    image_bytes = pymupdf.Pixmap(pix_base, pix_mask).tobytes()
                    ext = "png"

                # Filtra immagini inutili
                if not _is_useful_image(image_bytes, width, height):
                    continue

                # Filtra duplicati (stessa immagine usata su più pagine, es. header)
                img_hash = _image_hash(image_bytes)
                if img_hash in seen_hashes:
                    continue
                seen_hashes.add(img_hash)

                # Salva su disco
                filename = f"page_{page_num}_img_{xref}.{ext}"
                img_path = output_dir / filename
                with open(img_path, "wb") as f:
                    f.write(image_bytes)

                # Registra il path relativo (più portabile del path assoluto)
                rel_path = str(img_path)
                page_images.setdefault(page_num, []).append(rel_path)

            except Exception as e:
                print(f"[image_extractor] Errore xref {xref} pagina {page_num}: {e}")
                continue

    doc.close()
    return page_images


def save_image_registry(
    pdf_path: Path,
    image_records: list[dict],
    images_base_dir: Path,
) -> None:
    """
    Salva un registro JSON delle immagini processate.
    Utile per debug e per non riprocessare immagini già descritte.
    image_records è la lista costruita in pdf_processor durante l'ingestion.
    """
    doc_name = pdf_path.stem
    output_dir = images_base_dir / doc_name
    output_dir.mkdir(parents=True, exist_ok=True)

    registry = {
        "source": pdf_path.name,
        "total_images_processed": len(image_records),
        "images": image_records,
    }
    with open(output_dir / "registry.json", "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def get_images_for_chunks(chunk_ids: list[str], images_base_dir: Path) -> list[dict]:
    """
    Dato un insieme di chunk_ids recuperati dal RAG,
    restituisce le immagini collegate a quei chunk leggendo i manifest.

    Usata dal nodo 'respond' del grafo LangGraph per allegare immagini alla risposta.
    """
    results = []
    seen_files: set[str] = set()

    # Scansiona tutti i manifest presenti
    for manifest_path in images_base_dir.glob("*/manifest.json"):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        for img_entry in manifest["images"]:
            if img_entry["filename"] in seen_files:
                continue
            # Controlla se almeno uno dei chunk_ids richiesti è collegato
            if any(cid in img_entry["chunk_ids"] for cid in chunk_ids):
                results.append({
                    "source": manifest["source"],
                    "filename": img_entry["filename"],
                    "path": img_entry["path"],
                    "page": img_entry["page"],
                })
                seen_files.add(img_entry["filename"])

    return results