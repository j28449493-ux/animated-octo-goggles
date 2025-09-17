"""Generic scraper interfaces for company-specific collectors."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List


def normalize_job(raw: Dict) -> Dict:
    """Normalize a raw job dictionary to the tracker schema."""

    return {
        "company": raw.get("company", ""),
        "role": raw.get("role", ""),
        "location": raw.get("location", ""),
        "deadline": raw.get("deadline", ""),
        "apply_link": raw.get("apply_link", ""),
        "source": raw.get("source", "scraper:generic"),
        "notes": raw.get("notes", ""),
    }


def collect_jobs(fetch_fn: Callable[[], Iterable[Dict]]) -> List[Dict]:
    """Helper to transform an iterable of raw postings."""

    jobs: List[Dict] = []
    for raw in fetch_fn():
        jobs.append(normalize_job(raw))
    return jobs


__all__ = ["normalize_job", "collect_jobs"]
