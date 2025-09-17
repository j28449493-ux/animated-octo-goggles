"""Simple notification helpers for deadline reminders."""

from __future__ import annotations

from typing import Iterable


def notify(messages: Iterable[str]) -> None:
    """Print reminder messages to stdout."""

    for message in messages:
        print(f"[reminder] {message}")


__all__ = ["notify"]
