"""Google Calendar integration for deadline reminders."""

from __future__ import annotations

import datetime as dt
import os
from typing import Any, Dict

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

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class Calendar:
    """Lightweight wrapper around the Google Calendar API."""

    def __init__(self, calendar_id: str = "primary") -> None:
        if build is None or Credentials is None or InstalledAppFlow is None or Request is None:
            raise ModuleNotFoundError(
                "google-api-python-client and Google auth libraries are required for Calendar integration"
            )
        self.calendar_id = calendar_id
        self.creds = self._auth()
        self.service = build("calendar", "v3", credentials=self.creds)

    def _auth(self) -> Credentials:
        """Authenticate using OAuth, caching the token for future runs."""

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

    def add_deadline(self, title: str, deadline_iso: str, url: str | None = None) -> Dict[str, Any]:
        """Create a calendar event for a job application deadline."""

        start = dt.datetime.fromisoformat(deadline_iso)
        end = start + dt.timedelta(hours=1)
        body = {
            "summary": title,
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
            "description": url or "",
        }
        return self.service.events().insert(calendarId=self.calendar_id, body=body).execute()


__all__ = ["Calendar"]
