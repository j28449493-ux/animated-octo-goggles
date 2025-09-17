# SWE Internship Agent — Python Starter Kit

A modular Python workflow that **finds internships**, **stores them in Google Sheets**, **generates tailored materials**, and **creates deadline reminders**.

Designed to be practical, easy to extend, and portfolio-worthy. Drop this in a repo and iterate.

---

## 🧱 Project Structure

```
internship-agent/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ src/
│  ├─ main.py
│  ├─ config.py
│  ├─ sources/
│  │  ├─ simplify_client.py
│  │  ├─ rss_client.py
│  │  └─ company_scrapers/
│  │     ├─ amazon.py
│  │     └─ generic.py
│  ├─ tracker/
│  │  ├─ sheets_client.py
│  │  └─ schema.py
│  ├─ generator/
│  │  ├─ llm.py
│  │  ├─ resume_tailor.py
│  │  └─ cover_letter.py
│  ├─ reminders/
│  │  ├─ calendar_client.py
│  │  └─ notifier.py
│  └─ prep/
│     ├─ interview_bank.py
│     └─ mock_interview.py
└─ tests/
   └─ test_smoke.py
```

---

## 🔧 requirements.txt

```txt
python-dotenv
requests
feedparser
pydantic
pandas
google-api-python-client
google-auth
google-auth-oauthlib
python-dateutil
rich
tqdm
beautifulsoup4
```

Add your LLM client of choice (e.g., `openai` or `anthropic`) depending on which API you’ll call from `generator/llm.py`.

---

## 🔐 .env.example

```
# LLM
OPENAI_API_KEY=sk-...

# Google APIs (OAuth credentials live in credentials.json; token.json will be generated on first auth)
GOOGLE_SHEETS_SPREADSHEET_ID=your_sheet_id
GOOGLE_CALENDAR_ID=primary

# Sources
SIMPLIFY_API_KEY=...
SIMPLIFY_BASE=https://api.simplify.jobs
# Optional RSS feeds (comma-separated)
RSS_FEEDS=https://www.indeed.com/rss?q=SWE+Intern,https://boards.greenhouse.io/rss?board_token=...
```

Create a Google Cloud project, enable **Sheets API** and **Calendar API**, and download **OAuth client credentials** as `credentials.json` in the repo root.

---

## ⚙️ src/config.py

```python
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")
SIMPLIFY_API_KEY = os.getenv("SIMPLIFY_API_KEY")
SIMPLIFY_BASE = os.getenv("SIMPLIFY_BASE", "https://api.simplify.jobs")
RSS_FEEDS = [u.strip() for u in os.getenv("RSS_FEEDS", "").split(",") if u.strip()]
```

---

## 📊 src/tracker/schema.py

```python
from typing import List

COLUMNS: List[str] = [
    "added_at",         # ISO timestamp
    "company",
    "role",
    "location",
    "deadline",         # ISO date or blank
    "apply_link",
    "source",           # e.g., simplify, rss, scraper:amazon
    "status",           # new | interested | applied | interview | offer | rejected
    "resume_file",      # path or version tag
    "cover_letter_file",# path or version tag
    "notes",
]
```

---

## 📈 src/tracker/sheets_client.py

```python
from __future__ import annotations
from typing import List
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
from .schema import COLUMNS
from ..config import SPREADSHEET_ID

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

SHEET_NAME = "Internships"

class SheetsTracker:
    def __init__(self, spreadsheet_id: str = SPREADSHEET_ID):
        self.spreadsheet_id = spreadsheet_id
        self.creds = self._auth()
        self.service = build("sheets", "v4", credentials=self.creds)
        self._ensure_sheet()

    def _auth(self) -> Credentials:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def _ensure_sheet(self):
        sheets = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        titles = [s["properties"]["title"] for s in sheets["sheets"]]
        if SHEET_NAME not in titles:
            body = {"requests": [{"addSheet": {"properties": {"title": SHEET_NAME}}}]}
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
            # write header
            self.append_rows([COLUMNS])

    def append_rows(self, rows: List[List[str]]):
        body = {"values": rows}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()

    def add_job(self, job: dict):
        row = [
            datetime.utcnow().isoformat(),
            job.get("company", ""),
            job.get("role", ""),
            job.get("location", ""),
            job.get("deadline", ""),
            job.get("apply_link", ""),
            job.get("source", ""),
            "new",
            "",
            "",
            job.get("notes", ""),
        ]
        self.append_rows([row])
```

---

## 🌐 src/sources/simplify_client.py

```python
import requests
from typing import List, Dict
from ..config import SIMPLIFY_API_KEY, SIMPLIFY_BASE

class SimplifyClient:
    def __init__(self):
        self.base = SIMPLIFY_BASE.rstrip("/")
        self.headers = {"Authorization": f"Bearer {SIMPLIFY_API_KEY}"} if SIMPLIFY_API_KEY else {}

    def search(self, query: str = "software engineering intern", location: str | None = None) -> List[Dict]:
        # Adjust this to the actual Simplify API once you register
        url = f"{self.base}/v1/jobs/search"
        params = {"q": query, "type": "internship"}
        if location:
            params["location"] = location
        r = requests.get(url, params=params, headers=self.headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        jobs = []
        for item in data.get("results", []):
            jobs.append({
                "company": item.get("company"),
                "role": item.get("title"),
                "location": item.get("location", "Remote"),
                "deadline": item.get("deadline"),
                "apply_link": item.get("url"),
                "source": "simplify",
                "notes": item.get("source"),
            })
        return jobs
```

---

## 📰 src/sources/rss_client.py

```python
import feedparser
from typing import List, Dict

# pip install feedparser

def parse_feeds(feeds: list[str]) -> List[Dict]:
    jobs: List[Dict] = []
    for url in feeds:
        try:
            parsed = feedparser.parse(url)
            for e in parsed.entries:
                jobs.append({
                    "company": e.get("author", "Unknown"),
                    "role": e.get("title", ""),
                    "location": "",
                    "deadline": "",
                    "apply_link": e.get("link", ""),
                    "source": f"rss:{url}",
                    "notes": e.get("summary", ""),
                })
        except Exception as ex:
            print(f"RSS error for {url}: {ex}")
    return jobs
```

---

## 🧠 src/generator/llm.py

```python
import os
from typing import Literal

Model = Literal["gpt-4o-mini", "gpt-4.1", "gpt-4o"]

class LLM:
    def __init__(self, api_key: str | None = None, model: Model = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

    def complete(self, prompt: str) -> str:
        """Stub. Replace with actual OpenAI API call."""
        # For local testing, return echo
        return f"[DRAFT]\n{prompt[:4000]}"
```

---

## 🧾 src/generator/resume_tailor.py

```python
from .llm import LLM
from textwrap import dedent

SYSTEM = """You write concise, impact-oriented resume bullets using STAR framing. Optimize for ATS keywords and clarity."""

def tailor_resume_bullets(llm: LLM, job_title: str, job_desc: str, base_bullets: list[str]) -> list[str]:
    prompt = dedent(f"""
    System: {SYSTEM}

    Role: {job_title}
    Job Description:
    {job_desc}

    Base bullets:
    - """ + "\n    - ".join(base_bullets) + dedent("""

    Rewrite 4-5 bullets that best match the role. Keep each bullet under 25 words.
    Use strong verbs and quantify impact.
    """)
    out = llm.complete(prompt)
    return [b.strip("- ") for b in out.splitlines() if b.strip().startswith("-")]
```

---

## ✉️ src/generator/cover_letter.py

```python
from .llm import LLM
from textwrap import dedent

def cover_letter_draft(llm: LLM, company: str, role: str, job_desc: str, highlights: list[str]) -> str:
    prompt = dedent(f"""
    Write a 250-300 word cover letter for {role} at {company}.
    Weave in these highlights: {highlights}.
    Mirror the language of this job description:
    {job_desc}
    Keep tone: enthusiastic, concrete, professional. No fluff.
    """)
    return llm.complete(prompt)
```

---

## 🗓️ src/reminders/calendar_client.py

```python
from __future__ import annotations
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import datetime as dt
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]

class Calendar:
    def __init__(self, calendar_id: str = "primary"):
        self.calendar_id = calendar_id
        self.creds = self._auth()
        self.service = build("calendar", "v3", credentials=self.creds)

    def _auth(self) -> Credentials:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    def add_deadline(self, title: str, deadline_iso: str, url: str | None = None):
        start = dt.datetime.fromisoformat(deadline_iso)
        end = start + dt.timedelta(hours=1)
        body = {
            "summary": title,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
            "description": url or "",
        }
        return self.service.events().insert(calendarId=self.calendar_id, body=body).execute()
```

---

## 🤖 src/prep/interview_bank.py

```python
BANK = {
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
    ]
}
```

---

## 🧪 src/prep/mock_interview.py

```python
from .interview_bank import BANK
from random import choice


def ask_random(domain: str = "arrays") -> str:
    return choice(BANK.get(domain, BANK["behavioral"]))
```

---

## 🚂 src/main.py

```python
from rich import print
from tracker.sheets_client import SheetsTracker
from sources.simplify_client import SimplifyClient
from sources.rss_client import parse_feeds
from generator.llm import LLM
from generator.resume_tailor import tailor_resume_bullets
from generator.cover_letter import cover_letter_draft
from reminders.calendar_client import Calendar
from config import RSS_FEEDS, CALENDAR_ID

# 1) Fetch jobs from sources

def fetch_jobs(query: str = "software engineering intern"):
    jobs = []
    try:
        jobs += SimplifyClient().search(query=query)
    except Exception as e:
        print(f"[yellow]Simplify search failed:[/yellow] {e}")
    if RSS_FEEDS:
        jobs += parse_feeds(RSS_FEEDS)
    return jobs

# 2) Upsert into Sheets

def ingest_jobs(jobs: list[dict]):
    tracker = SheetsTracker()
    for j in jobs:
        tracker.add_job(j)
    print(f"[green]Added {len(jobs)} jobs to Sheets.[/green]")

# 3) Generate tailored materials (manual trigger per target)

def generate_materials(company: str, role: str, job_desc: str, base_bullets: list[str]):
    llm = LLM()
    bullets = tailor_resume_bullets(llm, role, job_desc, base_bullets)
    letter = cover_letter_draft(llm, company, role, job_desc, bullets[:3])
    return bullets, letter

# 4) Add deadline to calendar

def add_deadline(title: str, deadline_iso: str, url: str | None = None):
    cal = Calendar(calendar_id=CALENDAR_ID)
    event = cal.add_deadline(title, deadline_iso, url=url)
    print(f"[blue]Created calendar event:[/blue] {event.get('htmlLink')}")

if __name__ == "__main__":
    jobs = fetch_jobs()
    ingest_jobs(jobs)
    print("[bold]Done.[/bold]")
```

---

## ✅ First-Run Checklist

1. Create a **Google Sheet** and put its ID into `.env` as `GOOGLE_SHEETS_SPREADSHEET_ID`.
2. Enable **Google Sheets** + **Calendar** APIs; save OAuth `credentials.json` to repo root.
3. Copy `.env.example` → `.env` and fill values.
4. `pip install -r requirements.txt`
5. `python src/main.py` → authorize Google in browser on first run.

---

## ▶️ Example Usage

* **Pull postings** and send to Sheets:

  ```bash
  python src/main.py
  ```
* **Generate materials** (you’d wire this behind a CLI or small FastAPI app):

  ```python
  bullets, letter = generate_materials(
      company="Acme",
      role="Software Engineer Intern",
      job_desc="We use Python, AWS, React...",
      base_bullets=[
          "Built Python ETL to process 2M rows daily",
          "Deployed serverless API on AWS Lambda",
          "Implemented Dijkstra and BFS for routing feature",
      ],
  )
  print(bullets)
  print(letter)
  ```
* **Add a deadline**:

  ```python
  add_deadline("Acme SWE Intern — Apply", "2025-10-01T12:00:00", url="https://jobs.acme.com/apply")
  ```

---

## 🧭 Next Steps / Enhancements

* **Company scrapers**: add `src/sources/company_scrapers/amazon.py` with a simple HTML fetch + parse → normalize to schema.
* **De-duplication**: Keep a hash of `company|role|apply_link` in a separate sheet or local cache.
* **FastAPI UI**: Minimal endpoints to trigger fetch, view jobs, and generate materials.
* **File outputs**: Save generated cover letters to `/output/{company}-{role}.md` and reference in Sheets.
* **Status sync**: CLI commands `mark-applied`, `mark-interview` to update rows.
* **Airtable/Notion backend**: swap Sheets client when you outgrow Sheets.
* **Interview prep**: script to quiz you daily based on weak areas.

---

## 🆘 Troubleshooting

* **Sheets/Calendar auth loop** → delete `token.json` and re-run.
* **API quotas** → add retries + backoff.
* **LLM cost control** → batch prompts; use smaller models for drafts.

---

**License**: MIT (feel free to use/modify).
