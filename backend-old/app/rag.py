import requests
from backend.app.config import OLLAMA_URL, GENERATION_MODEL

# ---------------------------------------
# Ollama generation
# ---------------------------------------
def ollama_generate(prompt, model=GENERATION_MODEL):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_URL, json=payload)
    return response.json()["response"]

# ---------------------------------------
# Retrieval
# ---------------------------------------
def retrieve_relevant_chunks(query, collection, n_results=4):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0], results["metadatas"][0]

# ---------------------------------------
# Prompt building
# ---------------------------------------
def build_rag_prompt(question, retrieved_chunks):
    context_text = "\n\n---\n\n".join(retrieved_chunks)
    
    prompt = f"""
You are a helpful IT support assistant. Use ONLY the information in the context below to answer the question. 
If the answer is not in the context, say you don't have enough information.

Context:
{context_text}

---

Question: {question}

Answer clearly and concisely:
"""
    return prompt

# ---------------------------------------
# RAG answer
# ---------------------------------------
def rag_answer(question, collection):
    # Step 1: Retrieve chunks
    chunks, metadata = retrieve_relevant_chunks(question, collection)
    
    # Step 2: Build prompt
    prompt = build_rag_prompt(question, chunks)
    
    # Step 3: Generate answer using your local model
    answer = ollama_generate(prompt)
    
    return answer
