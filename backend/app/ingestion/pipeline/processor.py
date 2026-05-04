import hashlib
from .chunker import chunk_text
from .embedder import embed

def compute_hash(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def process_document(doc):
    text = doc["content"]
    file_hash = compute_hash(text)

    chunks = chunk_text(text)
    embeddings = embed(chunks)

    return {
        "doc_id": doc["id"],
        "name": doc["name"],
        "hash": file_hash,
        "chunks": chunks,
        "embeddings": embeddings,
        "metadata": doc.get("metadata", {})
    }
