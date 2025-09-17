"""Example scraper for Amazon internship listings."""

from __future__ import annotations

from typing import Dict, Iterable

try:  # pragma: no cover - optional dependency
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    requests = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    from bs4 import BeautifulSoup
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    BeautifulSoup = None  # type: ignore[assignment]

BASE_URL = "https://www.amazon.jobs/en/search"


def fetch_listings(keyword: str = "software", location: str | None = None) -> Iterable[Dict]:
    """Yield normalized Amazon postings scraped from the search results page."""

    if requests is None:
        raise ModuleNotFoundError("requests is required to fetch Amazon listings")
    if BeautifulSoup is None:
        raise ModuleNotFoundError("beautifulsoup4 is required to parse Amazon listings")
    params = {"base_query": keyword, "category[]": "software-development", "job_type": "Internship"}
    if location:
        params["location"] = location
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for card in soup.select("div.job-tile"):  # pragma: no cover - requires network
        title = card.select_one("h3.job-title")
        link = card.select_one("a.job-link")
        location_el = card.select_one("p.location-and-id")
        yield {
            "company": "Amazon",
            "role": title.text.strip() if title else "",
            "location": location_el.text.strip() if location_el else "",
            "deadline": "",
            "apply_link": f"https://www.amazon.jobs{link['href']}" if link and link.get("href") else "",
            "source": "scraper:amazon",
            "notes": "",
        }


__all__ = ["fetch_listings"]
