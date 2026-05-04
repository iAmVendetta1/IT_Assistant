import os
from .base import BaseSource
from app.connectors.itglue_client import ITGlueClient

class ITGlueSource(BaseSource):
    name = "itglue"
    collection_name = "itglue"

    def is_available(self):
        return bool(os.getenv("ITGLUE_API_KEY"))

    def fetch_documents(self):
        client = ITGlueClient(api_key=os.getenv("ITGLUE_API_KEY"))
        return client.get_documents()
