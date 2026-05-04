import os
from .base import BaseSource
from app.connectors.autotask_client import AutoTaskClient

class AutoTaskSource(BaseSource):
    name = "autotask"
    collection_name = "autotask"

    def is_available(self):
        return bool(os.getenv("AUTOTASK_API_KEY"))

    def fetch_documents(self):
        client = AutoTaskClient(api_key=os.getenv("AUTOTASK_API_KEY"))
        return client.get_documents()
