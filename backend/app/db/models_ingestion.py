from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.database import Base

class IngestedDocument(Base):
    __tablename__ = "ingested_documents"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    collection = Column(String, nullable=False)
    chunk_count = Column(Integer, nullable=False)
    extra_metadata = Column(JSON)
    ingested_at = Column(DateTime, server_default=func.now())
