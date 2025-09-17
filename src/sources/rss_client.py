"""RSS feed ingestion utilities."""

from __future__ import annotations

from typing import Dict, List

try:  # pragma: no cover - optional dependency
    import feedparser
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    feedparser = None  # type: ignore[assignment]


def parse_feeds(feeds: List[str]) -> List[Dict]:
    """Convert RSS feeds into normalized job records."""

    if feedparser is None:
        raise ModuleNotFoundError("feedparser is required to parse RSS feeds")
    jobs: List[Dict] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
        except Exception as exc:  # pragma: no cover - depends on feed
            print(f"RSS error for {url}: {exc}")
            continue
        for entry in parsed.entries:
            jobs.append(
                {
                    "company": entry.get("author", "Unknown"),
                    "role": entry.get("title", ""),
                    "location": "",
                    "deadline": "",
                    "apply_link": entry.get("link", ""),
                    "source": f"rss:{url}",
                    "notes": entry.get("summary", ""),
                }
            )
    return jobs


__all__ = ["parse_feeds"]
