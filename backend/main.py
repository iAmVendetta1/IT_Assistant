from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import chromadb
import os

load_dotenv()

from app.routes.conversations import router as conversations_router
from app.routes.ingestion import router as ingestion_router
from app.routes.chat import router as chat_router
from app.db.database import engine, Base
import app.db.models  # noqa: F401 — registers ORM models with Base
import app.db.models_ingestion  # noqa: F401 — registers ORM models with Base
from app.config import CHROMA_PATH
from app.routing import compute_centroids
from app.rag_pipeline import DCCAssistant

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    chroma = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collections = {
        col.name: chroma.get_or_create_collection(col.name, metadata={"hnsw:space": "cosine"})
        for col in chroma.list_collections()
    }
    centroids = compute_centroids(collections)
    app.state.assistant = DCCAssistant(collections, centroids)

    yield

app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(conversations_router)
app.include_router(ingestion_router)
app.include_router(chat_router)

# CORS
allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
