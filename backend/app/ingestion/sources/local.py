from pathlib import Path
from app.config import DOCS_DIR
from .base import BaseSource

class LocalSource(BaseSource):
    name = "local"
    collection_name = "local"

    def fetch_documents(self):
        docs = []
        for file in DOCS_DIR.glob("**/*"):
            if not file.is_file():
                continue

            if file.suffix.lower() in [".txt", ".md"]:
                text = file.read_text(encoding="utf-8", errors="ignore")

            elif file.suffix.lower() == ".docx":
                import docx
                doc = docx.Document(file)
                text = "\n".join(p.text for p in doc.paragraphs)

            else:
                continue

            docs.append({
                "id": str(file),
                "name": file.name,
                "content": text,
                "metadata": {"path": str(file)}
            })

        return docs
