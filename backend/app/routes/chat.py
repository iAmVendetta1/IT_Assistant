from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import requests
import json

from app.db.database import get_session
from app.db import crud_conversations as crud
from app.rag_pipeline import DCCAssistant
from app.routing import route_collection
from app.ingestion.pipeline.embedder import embed
from app.config import OLLAMA_URL, GENERATION_MODEL
from app.dependencies import get_current_user

router = APIRouter(tags=["Chat"])


@router.post("/conversations/{conversation_id}/stream")
async def stream_answer(
    conversation_id: UUID,
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    prompt = payload.get("prompt")

    messages = await crud.get_messages(
        session,
        conversation_id,
        user_id=user_id
    )

    formatted = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]

    # Build prompt using pipeline logic
    assistant = request.app.state.assistant

    # Embed query once, reuse for routing and retrieval
    q_emb = embed([prompt])[0]

    # Route to correct collection
    collection = route_collection(
        prompt,
        assistant.collections,
        assistant.centroids,
        q_emb
    )

    # Retrieve relevant chunks FROM that collection
    chunks, metadatas = assistant._retrieve_relevant_chunks(
        q_emb,
        collection,
        n_results=10
    )

    if not chunks:
        def no_context():
            yield json.dumps({"response": "I don't have any information relevant to that question in my knowledge base."}) + "\n"
        return StreamingResponse(no_context(), media_type="application/json")

    # Build prompt with context
    prompt_text = assistant._build_prompt(
        formatted,
        chunks,
        metadatas,
        prompt
    )

    # Call Ollama
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": GENERATION_MODEL,
            "prompt": prompt_text,
            "stream": True
        },
        stream=True
    )

    # Stream tokens back
    def generate():
        for line in response.iter_lines():
            if not line:
                continue

            try:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response")

                if token:
                    yield json.dumps({"response": token}) + "\n"

            except Exception:
                continue

    return StreamingResponse(generate(), media_type="application/json")