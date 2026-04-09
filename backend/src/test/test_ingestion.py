"""
Esegui con: uv run python scripts/test_ingestion.py
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.chroma_service import similarity_search
from services.pdf_processor import process_and_ingest_pdf


# 1. Ingestisci un PDF di test
result = process_and_ingest_pdf(
    Path("data/base_knowledge/2510.03623v1.pdf"),
    uploaded_by="system",
)
print("Ingestion:", result)

# 2. Fai una query di test
hits = similarity_search("Adversarial Attacks on XAI", k=3)
for doc, score in hits:
    print(f"\nScore: {score:.3f}")
    print(f"Source: {doc.metadata['source']}")
    print(f"Chunk: {doc.page_content[:200]}")