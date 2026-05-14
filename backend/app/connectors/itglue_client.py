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

    def _paginate(self, endpoint, params=None):
        page = 1
        while True:
            p = params.copy() if params else {}
            p["page[number]"] = page
            p["page[size]"] = 1000

            data = self._request("GET", endpoint, params=p)

            items = data.get("data") or []
            yield from items

            total_pages = data.get("meta", {}).get("total-pages", 1)
            if page >= total_pages:
                break

            page += 1
    
    def get_documents(self):
        docs = []

        for item in self._paginate("documents"):
            doc_id = item["id"]
            attrs = item["attributes"]

            title = attrs.get("name", f"doc_{doc_id}")
            body = self.clean_html(attrs.get("body", ""))
            org_id = attrs.get("organization-id", "")
            org_name = attrs.get("organization-name", "")

            docs.append({
                "id": f"itglue_{doc_id}",
                "name": title,
                "content": f"{title}\n\n{body}",
                "metadata": {
                    "organization_id": str(org_id),
                    "organization_name": org_name,
                }
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
