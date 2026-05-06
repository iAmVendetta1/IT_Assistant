from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import AskRequest, AnswerResponse
from app.rag_pipeline import DCCAssistant

from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_session
from app.db import crud_conversations as crud

from app.routes.conversations import router as conversations_router
from app.routes.ingestion import router as ingestion_router
from app.routes.chat import router as chat_router
from app.db.database import engine
from app.db.models_ingestion import Base as IngestionBase
from app.db.models import Base as ConversationBase

app = FastAPI()

# Routers
app.include_router(conversations_router)
app.include_router(ingestion_router)
app.include_router(chat_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(IngestionBase.metadata.create_all)
        await conn.run_sync(ConversationBase.metadata.create_all)

# Health check
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/ask/{conversation_id}", response_model=AnswerResponse)
async def ask_question(conversation_id: UUID, payload: AskRequest, session: AsyncSession = Depends(get_session)):
    if not hasattr(app.state, "assistant"):
        return AnswerResponse(
            answer="The assistant is not initialized. Please run /ingest/all first.",
            collection="none",
            sources=[]
        )

    user_msg = payload.message

    # Just call the assistant – no DB writes here
    result = app.state.assistant.ask([
        {"role": "user", "content": user_msg}
    ])

    return AnswerResponse(
        answer=result["answer"],
        collection=result["collection"],
        sources=result["sources"]
    )

