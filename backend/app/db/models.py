import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    category = Column(Text)
    source_id = Column(Text)
    raw_text = Column(Text, nullable=False)
    extra_metadata = Column(JSON, default={})
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)

    # NEW FIELDS
    client_id = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_vector_id = Column(String)
    extra_metadata = Column(JSON, default={})

    # NEW FIELD
    client_id = Column(String, nullable=True)

    document = relationship("Document", back_populates="chunks")

# Conversation + Message models (add to app/db/models.py)

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    title = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True
    )
    user_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

