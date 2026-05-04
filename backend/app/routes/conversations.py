from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_session
from app.db import crud_conversations as crud

router = APIRouter(prefix="/conversations", tags=["Conversations"])

FAKE_USER = "local_dev_user"


# -----------------------------
# Create conversation
# -----------------------------
@router.post("")
async def create_conversation(
    title: str | None = None,
    session: AsyncSession = Depends(get_session)
):
    # Always enforce a default title
    default_title = title or f"Conversation – {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}"

    convo = await crud.create_conversation(
        session,
        user_id=FAKE_USER,
        title=default_title
    )

    return {"id": convo.id, "title": convo.title}

# -----------------------------
# Get Conversations
# -----------------------------
@router.get("")
async def list_conversations(session: AsyncSession = Depends(get_session)):
    convos = await crud.list_conversations(session, user_id=FAKE_USER)

    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at
        }
        for c in convos
    ]

# -----------------------------
# Get conversation + messages
# -----------------------------
@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    convo = await crud.get_conversation(session, conversation_id, user_id=FAKE_USER)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    messages = await crud.get_messages(session, conversation_id, user_id=FAKE_USER)

    return {
        "id": convo.id,
        "title": convo.title,
        "messages": [{"role": m.role, "content": m.content} for m in messages]
    }

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    deleted = await crud.delete_conversation(session, conversation_id, user_id=FAKE_USER)
    if not deleted:
        raise HTTPException(404, "Conversation not found")
    return {"status": "ok"}

# -----------------------------
# Add message
# -----------------------------
@router.post("/{conversation_id}/messages")
async def add_message(
    conversation_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_session)
):
    role = payload["role"]
    content = payload["content"]

    convo = await crud.get_conversation(session, conversation_id, user_id=FAKE_USER)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    msg = await crud.add_message(session, conversation_id, FAKE_USER, role, content)
    return {"id": msg.id}

@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_session)
):
    new_title = payload.get("title")
    if not new_title:
        raise HTTPException(400, "Missing title")

    convo = await crud.rename_conversation(
        session, conversation_id, new_title, user_id=FAKE_USER
    )

    if not convo:
        raise HTTPException(404, "Conversation not found")

    return {"id": convo.id, "title": convo.title}
