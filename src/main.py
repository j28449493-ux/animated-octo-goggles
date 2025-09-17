"""Command-line entry points for the internship assistant workflow."""

from __future__ import annotations

from typing import Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    from rich import print as rich_print
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def rich_print(*args: object, **kwargs: object) -> None:
        """Fallback printer when ``rich`` is not installed."""

        print(*args, **kwargs)

from config import CALENDAR_ID, RSS_FEEDS
from generator.cover_letter import cover_letter_draft
from generator.llm import LLM
from generator.resume_tailor import tailor_resume_bullets
from reminders.calendar_client import Calendar
from sources.rss_client import parse_feeds
from sources.simplify_client import SimplifyClient
from tracker.sheets_client import SheetsTracker


def fetch_jobs(query: str = "software engineering intern") -> List[dict]:
    """Collect internship listings from configured sources."""

    jobs: List[dict] = []
    try:
        jobs.extend(SimplifyClient().search(query=query))
    except Exception as exc:  # pragma: no cover - network errors vary
        rich_print(f"[yellow]Simplify search failed:[/yellow] {exc}")
    if RSS_FEEDS:
        jobs.extend(parse_feeds(RSS_FEEDS))
    return jobs


def ingest_jobs(jobs: Iterable[dict]) -> None:
    """Persist fetched jobs into the Google Sheet tracker."""

    tracker = SheetsTracker()
    count = 0
    for job in jobs:
        tracker.add_job(job)
        count += 1
    rich_print(f"[green]Added {count} jobs to Sheets.[/green]")


def generate_materials(
    company: str,
    role: str,
    job_desc: str,
    base_bullets: List[str],
) -> Tuple[List[str], str]:
    """Create tailored resume bullets and a cover letter draft for a posting."""

    llm = LLM()
    bullets = tailor_resume_bullets(llm, role, job_desc, base_bullets)
    letter = cover_letter_draft(llm, company, role, job_desc, bullets[:3])
    return bullets, letter


def add_deadline(title: str, deadline_iso: str, url: str | None = None) -> None:
    """Add an application deadline event to the configured calendar."""

    cal = Calendar(calendar_id=CALENDAR_ID)
    event = cal.add_deadline(title, deadline_iso, url=url)
    rich_print(f"[blue]Created calendar event:[/blue] {event.get('htmlLink')}")


def main() -> None:
    """Default CLI routine for fetching jobs and saving them to Sheets."""

    jobs = fetch_jobs()
    ingest_jobs(jobs)
    rich_print("[bold]Done.[/bold]")


if __name__ == "__main__":  # pragma: no cover - CLI invocation
    main()
