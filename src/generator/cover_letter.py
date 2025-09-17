"""Cover letter generation helpers."""

from __future__ import annotations

from textwrap import dedent
from typing import List

from .llm import LLM


def cover_letter_draft(
    llm: LLM,
    company: str,
    role: str,
    job_desc: str,
    highlights: List[str],
) -> str:
    """Ask the configured language model to create a cover letter draft."""

    prompt = dedent(
        f"""
        Write a 250-300 word cover letter for {role} at {company}.
        Weave in these highlights: {highlights}.
        Mirror the language of this job description:
        {job_desc}
        Keep tone: enthusiastic, concrete, professional. No fluff.
        """
    )
    return llm.complete(prompt)
