"""Curated interview question bank for quick practice prompts."""

from __future__ import annotations

from typing import Dict, List

BANK: Dict[str, List[str]] = {
    "arrays": [
        "Two Sum",
        "Best Time to Buy and Sell Stock",
        "Product of Array Except Self",
    ],
    "graphs": [
        "Number of Islands",
        "Clone Graph",
    ],
    "behavioral": [
        "Tell me about a time you disagreed with a teammate.",
        "Describe a challenging bug you fixed.",
    ],
}


__all__ = ["BANK"]
