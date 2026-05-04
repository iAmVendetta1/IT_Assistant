from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL

embedder = SentenceTransformer(EMBEDDING_MODEL)

def embed(texts):
    return embedder.encode(texts).tolist()
