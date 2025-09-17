"""Client for fetching internships from the Simplify API."""

from __future__ import annotations

from typing import Dict, List

try:  # pragma: no cover - optional dependency
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]

from src.config import SIMPLIFY_API_KEY, SIMPLIFY_BASE


class SimplifyClient:
    """Thin wrapper around Simplify's job search endpoint."""

    def __init__(self) -> None:
        self.base = SIMPLIFY_BASE.rstrip("/")
        self.headers = {"Authorization": f"Bearer {SIMPLIFY_API_KEY}"} if SIMPLIFY_API_KEY else {}

    def search(self, query: str = "software engineering intern", location: str | None = None) -> List[Dict]:
        """Search for internship postings using the Simplify API."""

        if requests is None:
            raise ModuleNotFoundError("requests is required for SimplifyClient")
        url = f"{self.base}/v1/jobs/search"
        params = {"q": query, "type": "internship"}
        if location:
            params["location"] = location
        response = requests.get(url, params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        jobs = []
        for item in data.get("results", []):
            jobs.append(
                {
                    "company": item.get("company"),
                    "role": item.get("title"),
                    "location": item.get("location", "Remote"),
                    "deadline": item.get("deadline"),
                    "apply_link": item.get("url"),
                    "source": "simplify",
                    "notes": item.get("source"),
                }
            )
        return jobs


__all__ = ["SimplifyClient"]
