"""
Usato per creare la conoscenza di base del chat bot.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) 
from services.pdf_processor import ingest_base_knowledge


if __name__ == "__main__":
    print("Avvio ingestion documenti base_knowledge...")
    results = ingest_base_knowledge(Path("data/base_knowledge"))

    print("\n--- Riepilogo ---")
    for r in results:
        status = r["status"]
        source = r["source"]
        if status == "success":
            print(f"✓ {source}: {r['chunks_ingested']} chunk embeddati")
        elif status == "skipped":
            print(f"→ {source}: già presente, saltato")
        else:
            print(f"✗ {source}: errore — {r.get('reason', '?')}")