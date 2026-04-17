# connectors/itglue_client.py

from .base_client import BaseClient

SAFE_ITGLUE_TYPES = {
    "documents",
    "checklists",
    "configurations",
    "contacts",
    "locations",
    "vendors",
    "licensing",
    "printers",
    "ups",
    "mobile-devices",
    "voice",
    "wireless",
    "vpn-tunnels",
    "internet-wan",
    "lan",
    "file-sharing"
}

class ITGlueClient(BaseClient):
    def __init__(self, api_key):
        super().__init__(
            base_url="https://api.itglue.com",
            headers={
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
        )
    
    def get_documents(self):
        docs = []

        for item in self._paginate("documents"):
            doc_id = item["id"]
            attrs = item["attributes"]

            title = attrs.get("name", f"doc_{doc_id}")
            body = self.clean_html(attrs.get("body", ""))

            docs.append({
                "source": f"itglue_{doc_id}",
                "text": f"{title}\n\n{body}"
            })

        return docs

    def update_document(self, doc_id, new_body):
        """Write-back support for corrections."""
        payload = {
            "data": {
                "type": "documents",
                "id": doc_id,
                "attributes": {
                    "body": new_body
                }
            }
        }
        return self._request("PATCH", f"documents/{doc_id}", data=payload)
