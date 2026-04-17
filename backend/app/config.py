from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

CHROMA_PATH = BASE_DIR / "chroma_store"

OLLAMA_URL = "http://localhost:11434/api/generate"
GENERATION_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
