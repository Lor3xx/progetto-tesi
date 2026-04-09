from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.llm_client import llm, embeddings

# Test LLM
print(llm.invoke("Ciao, chi sei?"))

# Test embedding
vec = embeddings.embed_query("cybersecurity threat")
print(f"Dimensione vettore: {len(vec)}")