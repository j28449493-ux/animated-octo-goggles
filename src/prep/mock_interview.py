"""Utilities for quick interview practice sessions."""

from __future__ import annotations

from random import choice

from .interview_bank import BANK


def ask_random(domain: str = "arrays") -> str:
    """Return a random question from the specified domain."""

    return choice(BANK.get(domain, BANK["behavioral"]))


__all__ = ["ask_random"]
