import chromadb
from app.config import CHROMA_PATH
from app.db.database import AsyncSessionLocal
from app.ingestion.sources.local import LocalSource
from app.ingestion.sources.itglue import ITGlueSource
from app.ingestion.sources.autotask import AutoTaskSource
from app.ingestion.pipeline.processor import process_document
from app.ingestion.pipeline.storage import get_collection, store_processed_doc
from app.routing import compute_centroids

async def ingest_all():
    async with AsyncSessionLocal() as db:
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        collections = {}

        sources = [
            LocalSource(),
            ITGlueSource(),
            AutoTaskSource()
        ]

        for source in sources:
            if not source.is_available():
                print(f"Skipping {source.name} — unavailable")
                continue

            docs = source.fetch_documents()
            if not docs:
                print(f"No documents found for {source.name}")
                continue

            col = get_collection(chroma_client, source.collection_name)
            collections[source.collection_name] = col

            for doc in docs:
                processed = process_document(doc)
                await store_processed_doc(col, processed, db)

        centroids = compute_centroids(collections)
        return collections, centroids
