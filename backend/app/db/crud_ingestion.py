# app/db/crud_ingestion.py

from sqlalchemy.orm import Session
from app.db.models_ingestion import IngestedDocument

async def save_ingestion_record(db, doc_id, name, hash, collection, chunk_count, metadata):
    record = IngestedDocument(
        id=doc_id,
        name=name,
        hash=hash,
        collection=collection,
        chunk_count=chunk_count,
        extra_metadata=metadata
    )

    await db.merge(record)
    await db.commit()

