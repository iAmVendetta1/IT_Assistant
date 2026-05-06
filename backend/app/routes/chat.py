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
from app.config import OLLAMA_URL, GENERATION_MODEL

router = APIRouter(tags=["Chat"])

FAKE_USER = "local_dev_user"


@router.post("/conversations/{conversation_id}/stream")
async def stream_answer(
    conversation_id: UUID,
    payload: dict,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    prompt = payload.get("prompt")

    # Get conversation messages
    messages = await crud.get_messages(
        session,
        conversation_id,
        user_id=FAKE_USER
    )

    formatted = [
        {"role": m.role, "content": m.content}
        for m in messages
    ]

    # Build prompt using YOUR pipeline logic
    assistant = request.app.state.assistant

    # Route to correct collection
    collection = route_collection(
        prompt,
        assistant.collections,
        assistant.centroids
    )

    # Retrieve relevant chunks FROM that collection
    chunks, metadatas = assistant._retrieve_relevant_chunks(
        prompt,
        collection,
        n_results=10
    )

    # Build prompt WITH context
    prompt_text = assistant._build_prompt(
        formatted,
        chunks,
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