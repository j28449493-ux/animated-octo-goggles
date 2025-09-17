"""Resume tailoring utilities."""

from __future__ import annotations

from textwrap import dedent
from typing import List

from .llm import LLM

SYSTEM_PROMPT = (
    "You write concise, impact-oriented resume bullets using STAR framing. "
    "Optimize for ATS keywords and clarity."
)


def tailor_resume_bullets(
    llm: LLM,
    job_title: str,
    job_desc: str,
    base_bullets: List[str],
) -> List[str]:
    """Generate refined resume bullets tailored to a job description."""

    bullets_section = "\n    - ".join(base_bullets) if base_bullets else ""
    prompt = dedent(
        f"""
        System: {SYSTEM_PROMPT}

        Role: {job_title}
        Job Description:
        {job_desc}

        Base bullets:
        - {bullets_section}

        Rewrite 4-5 bullets that best match the role. Keep each bullet under 25 words.
        Use strong verbs and quantify impact.
        """
    )
    output = llm.complete(prompt)
    return [line.strip("- ") for line in output.splitlines() if line.strip().startswith("-")]


__all__ = ["tailor_resume_bullets", "SYSTEM_PROMPT"]
