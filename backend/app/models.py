from pydantic import BaseModel
from typing import List

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class AskRequest(BaseModel):
    message: str

class AnswerResponse(BaseModel):
    answer: str
    collection: str
    sources: List[str]


