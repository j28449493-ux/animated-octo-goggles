"""RSS feed ingestion utilities."""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Set
from urllib.parse import urlparse

try:  # pragma: no cover - optional dependency
    import feedparser
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    feedparser = None  # type: ignore[assignment]

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting delay between feed requests (seconds)
FEED_REQUEST_DELAY = 1.0

# Common location patterns to extract from job descriptions
LOCATION_PATTERNS = [
    r"Location:\s*([^,\n]+)",
    r"Based in:\s*([^,\n]+)",
    r"Office:\s*([^,\n]+)",
    r"Remote|Work from home|WFH",
    r"([A-Z][a-z]+,\s*[A-Z]{2})",  # City, State format
    r"([A-Z][a-z\s]+,\s*[A-Z][a-z\s]+)",  # City, Country format
]

# Deadline patterns
DEADLINE_PATTERNS = [
    r"Apply by:\s*([^,\n]+)",
    r"Deadline:\s*([^,\n]+)",
    r"Applications close:\s*([^,\n]+)",
]


def _is_valid_rss_url(url: str) -> bool:
    """Validate that a URL looks like a proper RSS feed URL."""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


def _extract_location(entry: Dict) -> str:
    """Extract location information from RSS entry."""
    # Check common fields first
    if hasattr(entry, 'location') and entry.location:
        return entry.location.strip()
    
    # Search in summary/description
    content = entry.get("summary", "") + " " + entry.get("description", "")
    
    for pattern in LOCATION_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            location = match.group(1) if match.groups() else match.group(0)
            return location.strip()
    
    # Check tags for location information
    if hasattr(entry, 'tags'):
        for tag in entry.tags:
            tag_term = tag.get('term', '').lower()
            if any(loc_word in tag_term for loc_word in ['location', 'city', 'remote', 'office']):
                return tag.get('term', '').strip()
    
    return ""


def _extract_deadline(entry: Dict) -> str:
    """Extract deadline information from RSS entry."""
    content = entry.get("summary", "") + " " + entry.get("description", "")
    
    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            deadline_text = match.group(1).strip()
            # Try to parse common date formats
            try:
                # Handle various date formats
                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"]:
                    try:
                        parsed_date = datetime.strptime(deadline_text, date_format)
                        return parsed_date.date().isoformat()
                    except ValueError:
                        continue
                # If no format matches, return the raw text
                return deadline_text
            except Exception:
                return deadline_text
    
    return ""


def _create_job_record(entry: Dict, feed_url: str) -> Dict[str, str]:
    """Create a normalized job record from an RSS entry."""
    # Extract company name with fallbacks
    company = (
        entry.get("author", "") or 
        entry.get("dc_creator", "") or
        entry.get("publisher", "") or
        "Unknown"
    ).strip()
    
    # Extract role/title
    role = entry.get("title", "").strip()
    
    # Extract location and deadline
    location = _extract_location(entry)
    deadline = _extract_deadline(entry)
    
    # Get apply link
    apply_link = entry.get("link", "").strip()
    
    # Combine summary and content for notes
    notes_parts = []
    if entry.get("summary"):
        notes_parts.append(entry["summary"].strip())
    if entry.get("content") and entry["content"] != entry.get("summary"):
        content_text = entry["content"][0].get("value", "") if isinstance(entry["content"], list) else str(entry["content"])
        if content_text and content_text.strip() != entry.get("summary", "").strip():
            notes_parts.append(content_text.strip())
    
    notes = " | ".join(notes_parts)
    
    return {
        "company": company,
        "role": role,
        "location": location,
        "deadline": deadline,
        "apply_link": apply_link,
        "source": f"rss:{feed_url}",
        "notes": notes,
    }


def _generate_job_key(job: Dict[str, str]) -> str:
    """Generate a unique key for duplicate detection."""
    # Use company, role, and apply_link for uniqueness
    company = job.get("company", "").lower().strip()
    role = job.get("role", "").lower().strip()
    link = job.get("apply_link", "").strip()
    return f"{company}|{role}|{link}"


def parse_feeds(feeds: List[str]) -> List[Dict]:
    """Convert RSS feeds into normalized job records with improved error handling and data extraction."""
    
    if feedparser is None:
        raise ModuleNotFoundError("feedparser is required to parse RSS feeds")
    
    if not feeds:
        logger.info("No RSS feeds configured")
        return []
    
    jobs: List[Dict] = []
    seen_jobs: Set[str] = set()
    
    for i, url in enumerate(feeds):
        if not _is_valid_rss_url(url):
            logger.warning(f"Invalid RSS URL format: {url}")
            continue
            
        # Rate limiting - add delay between requests
        if i > 0:
            time.sleep(FEED_REQUEST_DELAY)
        
        try:
            logger.info(f"Fetching RSS feed: {url}")
            parsed = feedparser.parse(url)
            
            # Check if feed was parsed successfully
            if hasattr(parsed, 'bozo') and parsed.bozo:
                logger.warning(f"RSS feed may have issues: {url} - {getattr(parsed, 'bozo_exception', 'Unknown error')}")
            
            if not hasattr(parsed, 'entries') or not parsed.entries:
                logger.warning(f"No entries found in RSS feed: {url}")
                continue
                
            feed_jobs_count = 0
            duplicates_count = 0
            
            for entry in parsed.entries:
                try:
                    job = _create_job_record(entry, url)
                    
                    # Skip jobs with missing critical information
                    if not job["role"] or not job["apply_link"]:
                        logger.debug(f"Skipping job with missing title or link from {url}")
                        continue
                    
                    # Check for duplicates
                    job_key = _generate_job_key(job)
                    if job_key in seen_jobs:
                        duplicates_count += 1
                        logger.debug(f"Duplicate job found: {job['company']} - {job['role']}")
                        continue
                    
                    seen_jobs.add(job_key)
                    jobs.append(job)
                    feed_jobs_count += 1
                    
                except Exception as exc:
                    logger.error(f"Error processing entry from {url}: {exc}")
                    continue
            
            logger.info(f"Processed {feed_jobs_count} jobs from {url} ({duplicates_count} duplicates skipped)")
            
        except Exception as exc:
            logger.error(f"RSS feed error for {url}: {exc}")
            continue
    
    logger.info(f"Total jobs collected from RSS feeds: {len(jobs)}")
    return jobs


__all__ = ["parse_feeds"]
