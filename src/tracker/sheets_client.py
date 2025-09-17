"""Google Sheets tracker integration for internship listings."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Iterable, List

try:  # pragma: no cover - optional dependency for runtime integration
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    build = None  # type: ignore[assignment]
    Credentials = None  # type: ignore[assignment]
    InstalledAppFlow = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]

from config import SPREADSHEET_ID
from tracker.schema import COLUMNS

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_NAME = "Internships"


class SheetsTracker:
    """Wrapper for writing job postings to a Google Sheet."""

    def __init__(self, spreadsheet_id: str | None = SPREADSHEET_ID) -> None:
        if build is None or Credentials is None or InstalledAppFlow is None or Request is None:
            raise ModuleNotFoundError(
                "google-api-python-client and Google auth libraries are required for Sheets integration"
            )
        if not spreadsheet_id:
            raise ValueError("A spreadsheet ID must be configured before using SheetsTracker")
        self.spreadsheet_id = spreadsheet_id
        self.creds = self._auth()
        self.service = build("sheets", "v4", credentials=self.creds)
        self._ensure_sheet()

    def _auth(self) -> Credentials:
        """Authenticate the Sheets client, caching tokens locally."""

        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w", encoding="utf-8") as token:
                token.write(creds.to_json())
        return creds

    def _ensure_sheet(self) -> None:
        """Create the internships sheet if it does not already exist."""

        sheets = self.service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        titles = [sheet["properties"]["title"] for sheet in sheets["sheets"]]
        if SHEET_NAME not in titles:
            body = {"requests": [{"addSheet": {"properties": {"title": SHEET_NAME}}}]}
            self.service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body=body).execute()
            self.append_rows([COLUMNS])

    def append_rows(self, rows: Iterable[Iterable[str]]) -> None:
        """Append raw rows to the internships sheet."""

        values = [list(row) for row in rows]
        body = {"values": values}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body=body,
        ).execute()

    def add_job(self, job: Dict[str, str]) -> None:
        """Write a job posting to Sheets using the configured schema."""

        row = [
            datetime.utcnow().isoformat(),
            job.get("company", ""),
            job.get("role", ""),
            job.get("location", ""),
            job.get("deadline", ""),
            job.get("apply_link", ""),
            job.get("source", ""),
            "new",
            job.get("resume_file", ""),
            job.get("cover_letter_file", ""),
            job.get("notes", ""),
        ]
        self.append_rows([row])


__all__ = ["SheetsTracker"]
