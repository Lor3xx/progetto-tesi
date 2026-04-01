from services.chroma_service import get_vector_store

vector_store = get_vector_store()

result = vector_store.get(where={"chunk_type": "image_description"})
print(len(result["ids"]))

print(result)