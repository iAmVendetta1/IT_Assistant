# connectors/base_client.py

import time
import logging
import requests
from markdownify import markdownify

class BaseClient:
    def __init__(self, base_url, headers, max_retries=3, backoff=2):
        self.base_url = base_url
        self.headers = headers
        self.max_retries = max_retries
        self.backoff = backoff
        self.log = logging.getLogger(self.__class__.__name__)

    def _request(self, method, endpoint, params=None, data=None):
        url = f"{self.base_url}/{endpoint}"

        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data,
                    timeout=15
                )

                # Rate limit handling
                if response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 5))
                    self.log.warning(f"Rate limited. Waiting {wait}s...")
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.RequestException as e:
                self.log.error(f"Request failed ({attempt+1}/{self.max_retries}): {e}")
                time.sleep(self.backoff)

        raise RuntimeError(f"Failed after {self.max_retries} attempts: {url}")

    def _paginate(self, endpoint, params=None):
        """Handles pagination for APIs that return paginated results."""
        page = 1
        while True:
            p = params.copy() if params else {}
            p["page"] = page

            data = self._request("GET", endpoint, params=p)

            items = data.get("data") or data.get("items") or []
            if not items:
                break

            yield from items

            # Stop if no more pages
            if len(items) < p.get("page_size", 100):
                break

            page += 1

    def clean_html(self, html):
        """Convert HTML to Markdown for better embeddings."""
        return markdownify(html or "").strip()
