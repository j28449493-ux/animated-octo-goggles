"""Command-line entry points for the internship assistant workflow."""

from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

try:  # pragma: no cover - optional dependency
    from rich import print as rich_print
    from rich.logging import RichHandler
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def rich_print(*args: object, **kwargs: object) -> None:
        """Fallback printer when ``rich`` is not installed."""

        print(*args, **kwargs)
    
    RichHandler = None  # type: ignore[assignment]

from src.config import CALENDAR_ID, RSS_FEEDS
from src.generator.cover_letter import cover_letter_draft
from src.generator.llm import LLM
from src.generator.resume_tailor import tailor_resume_bullets
from src.reminders.calendar_client import Calendar
from src.sources.rss_client import parse_feeds
from src.sources.simplify_client import SimplifyClient
from src.tracker.sheets_client import SheetsTracker


def _setup_logging() -> None:
    """Configure logging with Rich handler if available, otherwise use basic config."""
    
    # Configure root logger
    log_level = logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if RichHandler:
        # Use Rich handler for better formatting
        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(rich_tracebacks=True)]
        )
    else:
        # Fallback to basic logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    # Set specific logger levels
    logging.getLogger("sources.rss_client").setLevel(logging.INFO)
    logging.getLogger("tracker.sheets_client").setLevel(logging.INFO)


# Initialize logging
_setup_logging()
logger = logging.getLogger(__name__)


def fetch_jobs(query: str = "software engineering intern") -> List[dict]:
    """Collect internship listings from configured sources."""

    logger.info(f"Starting job fetch with query: '{query}'")
    jobs = []
    
    # Simplify client (currently commented out)
    # try:
    #     logger.info("Fetching jobs from Simplify...")
    #     simplify_jobs = SimplifyClient().search(query=query)
    #     jobs.extend(simplify_jobs)
    #     logger.info(f"Found {len(simplify_jobs)} jobs from Simplify")
    # except Exception as exc:  # pragma: no cover - network errors vary
    #     logger.warning(f"Simplify search failed: {exc}")
    #     rich_print(f"[yellow]Simplify search failed:[/yellow] {exc}")
    
    # RSS feeds
    if RSS_FEEDS:
        logger.info(f"Processing {len(RSS_FEEDS)} RSS feeds...")
        try:
            rss_jobs = parse_feeds(RSS_FEEDS)
            jobs.extend(rss_jobs)
            logger.info(f"Successfully collected {len(rss_jobs)} jobs from RSS feeds")
        except Exception as exc:
            logger.error(f"RSS feed processing failed: {exc}")
            rich_print(f"[red]RSS feed processing failed:[/red] {exc}")
    else:
        logger.info("No RSS feeds configured")
    
    logger.info(f"Total jobs collected: {len(jobs)}")
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
