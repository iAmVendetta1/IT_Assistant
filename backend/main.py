from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ingestion import ingest_all
from app.routing import compute_centroids
from app.models import ChatRequest, AnswerResponse
from app.rag_pipeline import DCCAssistant

app = FastAPI()

# ---------------------------------------
# CORS
# ---------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------
# Startup: load collections + centroids + assistant
# ---------------------------------------
@app.on_event("startup")
def startup_event():
    print("Loading collections...")
    collections, centroids = ingest_all()

    app.state.collections = collections
    app.state.centroids = centroids
    app.state.assistant = DCCAssistant(collections, centroids)

    print("Backend ready.")

# ---------------------------------------
# Health check
# ---------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------------------------------------
# Main RAG endpoint (multi-turn)
# ---------------------------------------
@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: ChatRequest):
    # Convert Pydantic models to plain dicts
    messages = [m.dict() for m in payload.messages]

    result = app.state.assistant.ask(messages)

    return AnswerResponse(
        answer=result["answer"],
        collection=result["collection"],
        sources=result["sources"]
    )

# ---------------------------------------
# Existing diagnostics endpoints unchanged
# ---------------------------------------
@app.get("/health/details")
def health_details():
    collections = app.state.collections
    centroids = app.state.centroids

    details = {
        "status": "ok",
        "collection_count": len(collections),
        "collections": {},
        "centroid_count": len(centroids) if centroids else 0
    }

    for name, col in collections.items():
        try:
            count = col.count()
        except Exception:
            count = "unknown"

        details["collections"][name] = {
            "documents": count
        }

    return details

@app.get("/collections")
def list_collections():
    return {"collections": list(app.state.collections.keys())}

@app.get("/collections/{name}")
def get_collection_details(name: str):
    collections = app.state.collections

    if name not in collections:
        return {"error": f"Collection '{name}' not found."}

    col = collections[name]

    try:
        count = col.count()
        items = col.get(include=["metadatas", "documents"])
    except Exception as e:
        return {"error": str(e)}

    return {
        "name": name,
        "document_count": count,
        "sample_documents": items["documents"][:3],
        "sample_metadata": items["metadatas"][:3]
    }

@app.post("/reingest")
def reingest():
    collections, centroids = ingest_all()

    app.state.collections = collections
    app.state.centroids = centroids
    app.state.assistant = DCCAssistant(collections, centroids)

    return {
        "status": "success",
        "message": "Re-ingestion complete.",
        "collections": list(collections.keys())
    }
