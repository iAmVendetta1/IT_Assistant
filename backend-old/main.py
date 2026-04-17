from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.ingestion import ingest_all
from backend.app.routing import compute_centroids, route_collection
from backend.app.rag import rag_answer
from backend.app.models import QuestionRequest, AnswerResponse

app = FastAPI()

app = FastAPI()

# ---------------------------------------
# CORS (allow frontend to call backend)
# ---------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # during development, allow everything
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------
# Startup: load collections + centroids
# ---------------------------------------
@app.on_event("startup")
def startup_event():
    print("Loading collections...")
    collections = ingest_all()
    centroids = compute_centroids(collections)

    # Store in app.state for global access
    app.state.collections = collections
    app.state.centroids = centroids

    print("Backend ready.")

# ---------------------------------------
# Health check
# ---------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------------------------------------
# Main RAG endpoint
# ---------------------------------------
@app.post("/ask", response_model=AnswerResponse)
def ask_question(payload: QuestionRequest):
    question = payload.question

    # 1. Route to correct collection
    col = route_collection(
        question,
        app.state.collections,
        app.state.centroids
    )

    # 2. Run RAG
    answer = rag_answer(question, col)

    # 3. Extract sources (optional but useful)
    #    We can pull metadata from the collection
    #    for transparency/debugging.
    results = col.query(query_texts=[question], n_results=4)
    sources = [m["source"] for m in results["metadatas"][0]]

    return AnswerResponse(
        answer=answer,
        collection=col.name,
        sources=sources
    )

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
    # Re-run ingestion
    collections = ingest_all()

    # Recompute centroids
    centroids = compute_centroids(collections)

    # Update app state
    app.state.collections = collections
    app.state.centroids = centroids

    return {
        "status": "success",
        "message": "Re-ingestion complete.",
        "collections": list(collections.keys())
    }




