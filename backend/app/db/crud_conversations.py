from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Conversation, Message
import uuid
from uuid import UUID

# -----------------------------
# Create a conversation
# -----------------------------
async def create_conversation(session: AsyncSession, user_id: str, title: str | None = None):
    convo = Conversation(
        id=uuid.uuid4(),
        title=title or "New Conversation",
        user_id=user_id
    )
    session.add(convo)
    await session.commit()
    await session.refresh(convo)
    return convo

# -----------------------------
# List conversations for a user
# -----------------------------
async def list_conversations(session: AsyncSession, user_id: str):
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()


# -----------------------------
# Add a message
# -----------------------------
async def add_message(session: AsyncSession, conversation_id: UUID, user_id: str, role: str, content: str):
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


# -----------------------------
# Get a conversation (user‑isolated)
# -----------------------------
async def get_conversation(session: AsyncSession, conversation_id: UUID, user_id: str):
    stmt = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# -----------------------------
# Get messages (user‑isolated)
# -----------------------------
async def get_messages(session: AsyncSession, conversation_id: UUID, user_id: str):
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.asc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# -----------------------------
# Delete conversation (user‑isolated)
# -----------------------------
async def delete_conversation(session: AsyncSession, conversation_id: UUID, user_id: str):
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
    )
    convo = result.scalar_one_or_none()

    if not convo:
        return False

    await session.delete(convo)
    await session.commit()
    return True

async def rename_conversation(session: AsyncSession, conversation_id: UUID, title: str, user_id: str):
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
    )
    convo = result.scalar_one_or_none()

    if not convo:
        return None

    convo.title = title
    await session.commit()
    await session.refresh(convo)
    return convo
