import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chroma_service import get_vector_store

collection = get_vector_store()._collection
results = collection.get(include=["documents", "metadatas"])

output = Path(__file__).parent.parent.parent.parent / "evaluation" / "chunks.csv"

with open(output, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["text", "source", "page"])
    writer.writeheader()
    for doc, meta in zip(results["documents"], results["metadatas"]):
        if meta.get("chunk_type") == "image_description":
            continue
        writer.writerow({
            "text":   doc,
            "source": meta.get("source", "unknown"),
            "page":   meta.get("page_number", ""),
        })

print(f"Esportati {output}")