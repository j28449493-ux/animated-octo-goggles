"""Environment-driven configuration for the internship agent."""

from __future__ import annotations

import os
from typing import Iterable, List

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        """Fallback ``load_dotenv`` implementation when python-dotenv is absent."""

        return False


def _load_environment() -> None:
    """Load configuration variables from a ``.env`` file if available."""

    load_dotenv()


_load_environment()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
SPREADSHEET_ID: str | None = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
SIMPLIFY_API_KEY: str | None = os.getenv("SIMPLIFY_API_KEY")
SIMPLIFY_BASE: str = os.getenv("SIMPLIFY_BASE", "https://api.simplify.jobs")


def _parse_feeds(raw_value: str) -> List[str]:
    """Split the comma-delimited RSS feed string into individual URLs."""

    return [url.strip() for url in raw_value.split(",") if url.strip()]


RSS_FEEDS: List[str] = _parse_feeds(os.getenv("RSS_FEEDS", ""))

__all__: Iterable[str] = (
    "OPENAI_API_KEY",
    "SPREADSHEET_ID",
    "CALENDAR_ID",
    "SIMPLIFY_API_KEY",
    "SIMPLIFY_BASE",
    "RSS_FEEDS",
)
