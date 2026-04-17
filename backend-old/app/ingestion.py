from pathlib import Path
import hashlib
import docx
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from backend.app.config import DOCS_DIR, CHROMA_PATH, EMBEDDING_MODEL

# -----------------------------
# Embedding model
# -----------------------------
embedder = SentenceTransformer(EMBEDDING_MODEL)

def embed(texts):
    return embedder.encode(texts).tolist()

# -----------------------------
# Document loading
# -----------------------------
def load_documents(folder: Path):
    docs = []
    for file in folder.glob("*"):
        if file.suffix.lower() in [".txt", ".md"]:
            text = file.read_text(encoding="utf-8", errors="ignore")
            docs.append({"source": file.name, "text": text})

        elif file.suffix.lower() == ".docx":
            doc = docx.Document(file)
            text = "\n".join([para.text for para in doc.paragraphs])
            docs.append({"source": file.name, "text": text})

    return docs

# -----------------------------
# Hashing
# -----------------------------
def compute_hash(text: str):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# -----------------------------
# Chunking
# -----------------------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=200
)

# -----------------------------
# Ingestion logic
# -----------------------------
def ingest_all():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collections = {}

    for folder in DOCS_DIR.iterdir():
        if not folder.is_dir():
            continue

        collection_name = folder.name
        print(f"Ingesting collection: {collection_name}")

        docs = load_documents(folder)
        if not docs:
            print(f"Skipping empty folder: {collection_name}")
            continue

        col = chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        collections[collection_name] = col

        for doc in docs:
            text = doc["text"]
            file_hash = compute_hash(text)

            existing = col.get(where={"source": doc["source"]}, include=["metadatas"])

            if existing["metadatas"]:
                existing_hash = existing["metadatas"][0].get("file_hash")
                if existing_hash == file_hash:
                    print(f"Skipping unchanged document: {doc['source']}")
                    continue

                print(f"Updating document: {doc['source']}")
                col.delete(where={"source": doc["source"]})

            doc_chunks = splitter.split_text(text)

            chunks = []
            metadatas = []
            ids = []

            for j, chunk in enumerate(doc_chunks):
                chunks.append(chunk)
                metadatas.append({
                    "source": doc["source"],
                    "file_hash": file_hash
                })
                ids.append(f"{doc['source']}_chunk_{j}")

            embeddings = embed(chunks)

            col.add(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

        print(f"Finished collection: {collection_name}")

    return collections
