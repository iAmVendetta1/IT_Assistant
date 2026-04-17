from typing import List, Dict
import requests

from app.config import OLLAMA_URL, GENERATION_MODEL
from app.routing import route_collection
from app.ingestion import embed

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
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        return documents, metadatas

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
You are a helpful IT support assistant. Answer the user's question using ONLY the information provided in the context below.

The context provided is COMPLETE and AUTHORITATIVE. All necessary information is included.

Provide the COMPLETE answer with ALL relevant details from the context exactly as presented. Do not filter, omit, or reorganize information based on your interpretation.

Preserve any structure from the context (lists, steps, procedures) exactly as it appears.

Conversation history:
{history_text}

Context:
{context_text}

User's latest question:
{latest_user}

---

Answer (include all relevant information from the context):
""".strip()
        return prompt

    # ---- Main entrypoint ----
    def ask(self, messages: List[Dict[str, str]]):
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
        
        # DEBUG: Print what was retrieved
        print(f"DEBUG - Retrieved {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: {chunk[:200]}...")  # Show first 200 chars

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