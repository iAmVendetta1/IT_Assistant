from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.database import get_session
from app.db import crud_conversations as crud
from app.dependencies import get_current_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("")
async def create_conversation(
    title: str | None = None,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    convo = await crud.create_conversation(
        session,
        user_id=user_id,
        title=title or "New Conversation"
    )
    return {"id": convo.id, "title": convo.title}


@router.get("")
async def list_conversations(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    convos = await crud.list_conversations(session, user_id=user_id)
    return [
        {"id": c.id, "title": c.title, "created_at": c.created_at}
        for c in convos
    ]


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    convo = await crud.get_conversation(session, conversation_id, user_id=user_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    messages = await crud.get_messages(session, conversation_id, user_id=user_id)
    return {
        "id": convo.id,
        "title": convo.title,
        "messages": [{"role": m.role, "content": m.content} for m in messages]
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    deleted = await crud.delete_conversation(session, conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(404, "Conversation not found")
    return {"status": "ok"}


@router.post("/{conversation_id}/messages")
async def add_message(
    conversation_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    convo = await crud.get_conversation(session, conversation_id, user_id=user_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    msg = await crud.add_message(session, conversation_id, user_id, payload["role"], payload["content"])
    return {"id": msg.id}


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: UUID,
    payload: dict,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_current_user)
):
    new_title = payload.get("title")
    if not new_title:
        raise HTTPException(400, "Missing title")

    convo = await crud.rename_conversation(session, conversation_id, new_title, user_id=user_id)
    if not convo:
        raise HTTPException(404, "Conversation not found")

    return {"id": convo.id, "title": convo.title}
