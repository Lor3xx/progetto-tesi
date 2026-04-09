from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # aggiunge src/ al path
from services.chroma_service import similarity_search_prioritized, similarity_search_images

query = [
    "Adversarial Attacks on XAI",
    "cos'è il grey-box adversary?",
    "what is Adversarial Model?",
    "what is RENNERVATE?",
    "come funziona TVLA?",
    "cos'è SiamXBERT?",
    "Context-Aware Phishing Email Detection"
]


for q in query:
    hits = similarity_search_prioritized(q, k=5)
    images = similarity_search_images(q, k=3)
    sources = set(doc.metadata["source"] for doc, _ in hits)
    print(f"\nQuery: {q}")
    for doc, score in hits:
        print(f"\nScore: {score:.3f}")
        print(f"Source: {doc.metadata['source']}")
        print(f"Chunk id: {doc.metadata['chunk_id']}")
        print(f"Chunk: {doc.page_content[:200]}")
    print("-" * 50)
    for doc, score in images:
        if doc.metadata["source"] not in sources:
            continue  # mostra solo immagini da fonti già presenti nei chunk testuali
        print(f"\nImage Score: {score:.3f}")
        print(f"Image Source: {doc.metadata['source']}")
        print(f"Image Chunk: {doc.page_content[:200]}")
    print("==" * 50)