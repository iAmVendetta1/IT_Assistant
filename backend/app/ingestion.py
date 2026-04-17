import os
from pathlib import Path
import hashlib
import docx
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from app.config import DOCS_DIR, CHROMA_PATH, EMBEDDING_MODEL
from app.connectors.itglue_client import ITGlueClient
from app.connectors.autotask_client import AutoTaskClient

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
    chunk_size=5000,
    chunk_overlap=0
)

# -----------------------------
# Ingestion logic
# -----------------------------
def ingest_local_files(chroma_client, collections):
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

def ingest_itglue(chroma_client, collections):
    api_key = os.getenv("ITGLUE_API_KEY")
    if not api_key:
        print("ITGlue API key missing — skipping ingestion")
        return

    client = ITGlueClient(api_key=api_key)
    docs = client.get_documents()  # Must return list of {"source": "...", "text": "..."}

    collection_name = "itglue"
    col = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    collections[collection_name] = col

    print("Ingesting ITGlue documents...")

    for doc in docs:
        text = doc["text"]
        file_hash = compute_hash(text)

        existing = col.get(where={"source": doc["source"]}, include=["metadatas"])

        if existing["metadatas"]:
            existing_hash = existing["metadatas"][0].get("file_hash")
            if existing_hash == file_hash:
                print(f"Skipping unchanged ITGlue doc: {doc['source']}")
                continue

            print(f"Updating ITGlue doc: {doc['source']}")
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

    print("Finished ITGlue ingestion")

def ingest_autotask(chroma_client, collections):
    api_key = os.getenv("AUTOTASK_API_KEY")
    if not api_key:
        print("AutoTask API key missing — skipping ingestion")
        return

    client = AutoTaskClient(api_key=api_key)
    docs = client.get_documents()  # Must return list of {"source": "...", "text": "..."}

    collection_name = "autotask"
    col = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    collections[collection_name] = col

    print("Ingesting autotask documents...")

    for doc in docs:
        text = doc["text"]
        file_hash = compute_hash(text)

        existing = col.get(where={"source": doc["source"]}, include=["metadatas"])

        if existing["metadatas"]:
            existing_hash = existing["metadatas"][0].get("file_hash")
            if existing_hash == file_hash:
                print(f"Skipping unchanged AutoTask doc: {doc['source']}")
                continue

            print(f"Updating AutoTask doc: {doc['source']}")
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

    print("Finished AutoTask ingestion")

# ---- Cleanup ----
def cleanup_orphaned_documents(chroma_client, collections):
    """Remove documents from DB that no longer exist in the filesystem"""
    for folder in DOCS_DIR.iterdir():
        if not folder.is_dir():
            continue

        collection_name = folder.name
        col = chroma_client.get_or_create_collection(name=collection_name)

        # Get all docs currently in collection
        all_docs = col.get(include=[])  # Returns {"ids": [...], "metadatas": [...], "documents": [...]} or {"ids": [...], "metadatas": [...], "documents": []}

        # Get all filenames currently in folder
        current_files = {f.name for f in folder.glob("*") if f.suffix.lower() in [".txt", ".md", ".docx"]}

        # Delete entries for files that no longer exist
        for doc_id in all_docs["ids"]:
            source_name = doc_id.split("_chunk_")[0]  # Extract source from ID
            if source_name not in current_files:
                print(f"Deleting orphaned document: {source_name}")
                col.delete(where={"source": source_name})

# ---- Main ingestion orchestrator ----
def ingest_all():
    """Load or create Chroma client and ingest all documents"""
    import chromadb
    from app.routing import compute_centroids
    
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collections = {}

    cleanup_orphaned_documents(chroma_client, collections)
    ingest_local_files(chroma_client, collections)
    ingest_itglue(chroma_client, collections)
    ingest_autotask(chroma_client, collections)

    # Recompute centroids after ingestion
    centroids = compute_centroids(collections)

    return collections, centroids