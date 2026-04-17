# connectors/autotask_client.py

from .base_client import BaseClient

class AutoTaskClient(BaseClient):
    def __init__(self, api_key):
        super().__init__(
            base_url="https://webservices.autotask.net/rest/v1.0",
            headers={
                "ApiIntegrationCode": api_key,
                "Content-Type": "application/json"
            }
        )

    def get_tickets(self):
        docs = []

        for item in self._paginate("Tickets"):
            ticket_id = item.get("id")
            title = item.get("title", f"ticket_{ticket_id}")
            desc = self.clean_html(item.get("description", ""))

            docs.append({
                "source": f"autotask_{ticket_id}",
                "text": f"{title}\n\n{desc}"
            })

        return docs

    def update_ticket(self, ticket_id, note_text):
        """Append a note to a ticket."""
        payload = {
            "id": ticket_id,
            "description": note_text
        }
        return self._request("PATCH", f"Tickets/{ticket_id}", data=payload)
