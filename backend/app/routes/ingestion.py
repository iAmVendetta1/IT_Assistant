from fastapi import APIRouter, UploadFile, File, Form, Request
from app.ingestion.orchestrator import ingest_all
from app.ingestion.sources.local import LocalSource
from app.ingestion.sources.itglue import ITGlueSource
from app.ingestion.sources.autotask import AutoTaskSource
from app.ingestion.pipeline.processor import process_document
from app.ingestion.pipeline.storage import get_collection, store_processed_doc
from app.db.database import AsyncSessionLocal
from app.rag_pipeline import DCCAssistant
import chromadb
from app.config import CHROMA_PATH

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


# ---- Helper to get Chroma client ----
def get_chroma():
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


# ---- Ingest everything ----
@router.post("/all")
async def ingest_everything(request: Request):
    collections, centroids = await ingest_all()

    # Update global app state
    request.app.state.collections = collections
    request.app.state.centroids = centroids
    request.app.state.assistant = DCCAssistant(collections, centroids)

    return {
        "status": "ok",
        "collections": list(collections.keys()),
        "centroid_count": len(centroids),
    }


# ---- Ingest local documents ----
@router.post("/local")
async def ingest_local():
    async with AsyncSessionLocal() as db:
        chroma = get_chroma()
        source = LocalSource()

        docs = source.fetch_documents()
        col = get_collection(chroma, source.collection_name)

        for doc in docs:
            processed = process_document(doc)
            await store_processed_doc(col, processed, db)

        return {"status": "ok", "count": len(docs)}


# ---- Ingest ITGlue ----
@router.post("/itglue")
async def ingest_itglue():
    async with AsyncSessionLocal() as db:
        chroma = get_chroma()
        source = ITGlueSource()

        if not source.is_available():
            return {"status": "error", "message": "ITGlue API key missing"}

        docs = source.fetch_documents()
        col = get_collection(chroma, source.collection_name)

        for doc in docs:
            processed = process_document(doc)
            await store_processed_doc(col, processed, db)

        return {"status": "ok", "count": len(docs)}


# ---- Ingest AutoTask ----
@router.post("/autotask")
async def ingest_autotask():
    async with AsyncSessionLocal() as db:
        chroma = get_chroma()
        source = AutoTaskSource()

        if not source.is_available():
            return {"status": "error", "message": "AutoTask API key missing"}

        docs = source.fetch_documents()
        col = get_collection(chroma, source.collection_name)

        for doc in docs:
            processed = process_document(doc)
            await store_processed_doc(col, processed, db)

        return {"status": "ok", "count": len(docs)}


# ---- Ingest raw text ----
@router.post("/text")
async def ingest_text(name: str = Form(...), content: str = Form(...)):
    async with AsyncSessionLocal() as db:
        chroma = get_chroma()

        doc = {
            "id": f"manual_{name}",
            "name": name,
            "content": content,
            "metadata": {"source": "manual"}
        }

        processed = process_document(doc)
        col = get_collection(chroma, "manual")

        await store_processed_doc(col, processed, db)

        return {"status": "ok", "name": name}


# ---- Ingest uploaded file ----
@router.post("/file")
async def ingest_file(file: UploadFile = File(...)):
    async with AsyncSessionLocal() as db:
        chroma = get_chroma()

        text = (await file.read()).decode("utf-8", errors="ignore")

        doc = {
            "id": f"upload_{file.filename}",
            "name": file.filename,
            "content": text,
            "metadata": {"source": "upload"}
        }

        processed = process_document(doc)
        col = get_collection(chroma, "uploads")

        await store_processed_doc(col, processed, db)

        return {"status": "ok", "filename": file.filename}


