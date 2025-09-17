"""Schema definition for the internship tracking spreadsheet."""

from __future__ import annotations

from typing import List

COLUMNS: List[str] = [
    "added_at",  # ISO timestamp
    "company",
    "role",
    "location",
    "deadline",  # ISO date or blank
    "apply_link",
    "source",  # e.g., simplify, rss, scraper:amazon
    "status",  # new | interested | applied | interview | offer | rejected
    "resume_file",  # path or version tag
    "cover_letter_file",  # path or version tag
    "notes",
]


__all__ = ["COLUMNS"]
