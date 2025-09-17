"""Minimal language model wrapper used throughout the project."""

from __future__ import annotations

import os
from typing import Literal

Model = Literal["gpt-4o-mini", "gpt-4.1", "gpt-4o"]


class LLM:
    """Simple facade around an LLM provider."""

    def __init__(self, api_key: str | None = None, model: Model = "gpt-4o-mini") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def complete(self, prompt: str) -> str:
        """Return a completion for the supplied prompt."""

        # For local testing, return echo
        return f"[DRAFT]\n{prompt[:4000]}"


__all__ = ["LLM", "Model"]
