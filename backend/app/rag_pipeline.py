from typing import List, Dict
import requests
from app.ingestion.pipeline.embedder import embed

from app.config import OLLAMA_URL, GENERATION_MODEL, RETRIEVAL_DISTANCE_THRESHOLD
from app.routing import route_collection

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.database import AsyncSessionLocal

class DCCAssistant:
    def __init__(self, collections, centroids):
        self.collections = collections
        self.centroids = centroids

    # ---- Ollama call ----
    def _ollama_generate(self, prompt: str) -> str:
        payload = {
            "model": GENERATION_MODEL,
            "prompt": prompt,
            "stream": False
        }
        resp = requests.post(OLLAMA_URL, json=payload)
        resp.raise_for_status()
        return resp.json()["response"]

    # ---- Retrieval ----
    def _retrieve_relevant_chunks(self, query: str, collection, n_results: int = 5):
        query_embedding = embed([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        filtered = [
            (doc, meta)
            for doc, meta, dist in zip(documents, metadatas, distances)
            if dist <= RETRIEVAL_DISTANCE_THRESHOLD
        ]

        if not filtered:
            return [], []

        docs, metas = zip(*filtered)
        return list(docs), list(metas)

    # ---- Prompt building with history + context ----
    def _build_prompt(self, messages, context_chunks, latest_user):
        # Exclude the latest user message from history
        history_text = ""
        for m in messages[:-1]:
            role = m["role"].upper()
            history_text += f"{role}: {m['content']}\n"
        
        history_text = history_text.strip()
        context_text = "\n\n---\n\n".join(context_chunks)

        prompt = f"""
You are a helpful IT support assistant. Answer the user's question using ONLY the information provided in the context below. Do not add any information that is not present in the context.

When the context contains a list, a sequence of steps, or a procedure, you MUST include every item in full — do not stop early, summarize, or skip any steps.

Do not make editorial decisions about which parts of the context are relevant. If the context addresses the question, reproduce it completely and exactly as it appears.

Conversation history:
{history_text}

Context:
{context_text}

User's latest question:
{latest_user}

---

Answer:
""".strip()
        return prompt

    # ---- Main entrypoint ----
    def ask(self, messages: List[Dict[str, str]]):
        # If no collections exist yet, just return a simple response
        if not self.collections:
            return {
                "answer": "No information is available to answer your question yet.",
                "collection": "none",
                "sources": []
            }
        # 1. Get latest user message
        latest_user = next(
            (m["content"] for m in reversed(messages) if m["role"] == "user"),
            None
        )
        if not latest_user:
            return {
                "answer": "I didn't receive a user question.",
                "collection": "unknown",
                "sources": []
            }

        # 2. Route to collection
        collection = route_collection(
            latest_user,
            self.collections,
            self.centroids
        )

        # 3. Retrieve chunks
        chunks, metadatas = self._retrieve_relevant_chunks(latest_user, collection, n_results=10)

        if not chunks:
            return {
                "answer": "I don't have any information relevant to that question in my knowledge base.",
                "collection": collection.name,
                "sources": []
            }

        # 4. Build prompt with history + context
        prompt = self._build_prompt(messages, chunks, latest_user)

        # 5. Generate answer
        answer = self._ollama_generate(prompt)

        # 6. Extract sources
        sources = [m["source"] for m in metadatas]

        return {
            "answer": answer,
            "collection": collection.name,
            "sources": sources
        }