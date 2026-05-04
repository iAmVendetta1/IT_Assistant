import chromadb
import uuid
from app.config import CHROMA_PATH
from app.db.crud_ingestion import save_ingestion_record

def get_collection(client, name):
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

async def store_processed_doc(collection, processed, db):
    ids = []
    metadatas = []
    docs = []

    for i, chunk in enumerate(processed["chunks"]):
        chunk_id = f"{processed['doc_id']}_chunk_{i}"
        meta = {
            "source": processed["name"],
            "file_hash": processed["hash"],
            **processed["metadata"]
        }

        ids.append(chunk_id)
        metadatas.append(meta)
        docs.append(chunk)

    collection.add(
        ids=ids,
        documents=docs,
        embeddings=processed["embeddings"],
        metadatas=metadatas
    )

    await save_ingestion_record(
        db=db,
        doc_id=processed["doc_id"],
        name=processed["name"],
        hash=processed["hash"],
        collection=collection.name,
        chunk_count=len(processed["chunks"]),
        metadata=processed["metadata"]
    )

    await db.commit()
