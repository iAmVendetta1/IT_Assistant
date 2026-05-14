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
    def _retrieve_relevant_chunks(self, query: str, collection, n_results: int = 10):
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
    def _build_prompt(self, messages, context_chunks, metadatas, latest_user):
        history_text = ""
        for m in messages[:-1]:
            role = m["role"].upper()
            history_text += f"{role}: {m['content']}\n"

        history_text = history_text.strip()

        context_parts = []
        for chunk, meta in zip(context_chunks, metadatas):
            org = meta.get("organization_name", "")
            context_parts.append(f"[{org}]\n{chunk}" if org else chunk)
        context_text = "\n\n---\n\n".join(context_parts)

        prompt = f"""
You are a helpful IT support assistant. Answer the user's question using ONLY the information provided in the context below. Do not add any information that is not present in the context.

When the context contains a list, a sequence of steps, or a procedure, you MUST include every item in full — do not stop early, summarize, or skip any steps.

Do not make editorial decisions about which parts of the context are relevant. If the context addresses the question, reproduce it completely and exactly as it appears.

Each context chunk may be prefixed with an organization name in brackets (e.g. [Client A]). Always include that tag alongside your answer so the technician can confirm the information applies to their situation. If chunks from multiple organizations are relevant, note each one.

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
        if not self.collections:
            return {
                "answer": "No information is available to answer your question yet.",
                "collection": "none",
                "sources": []
            }

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

        collection = route_collection(
            latest_user,
            self.collections,
            self.centroids
        )

        chunks, metadatas = self._retrieve_relevant_chunks(latest_user, collection)

        if not chunks:
            return {
                "answer": "I don't have any information relevant to that question in my knowledge base.",
                "collection": collection.name,
                "sources": []
            }

        prompt = self._build_prompt(messages, chunks, metadatas, latest_user)

        answer = self._ollama_generate(prompt)

        sources = [m["source"] for m in metadatas]

        return {
            "answer": answer,
            "collection": collection.name,
            "sources": sources
        }
