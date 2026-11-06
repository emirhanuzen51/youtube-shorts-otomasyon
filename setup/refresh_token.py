#!/usr/bin/env python3
"""Refresh AnimAI Studio's YouTube OAuth token without printing it."""
import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "animai_youtube_refresh_token.txt"


def get_refresh_token(client_id: str, client_secret: str) -> str:
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8080"],
            }
        },
        SCOPES,
    )
    credentials = flow.run_local_server(port=8080, open_browser=True)
    if not credentials.refresh_token:
        raise RuntimeError("Google OAuth completed without returning a refresh token")
    return credentials.refresh_token


if __name__ == "__main__":
    client_id = os.environ.get("ANIMAI_YT_CLIENT_ID")
    client_secret = os.environ.get("ANIMAI_YT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Set ANIMAI_YT_CLIENT_ID and ANIMAI_YT_CLIENT_SECRET before running this script.")
        sys.exit(1)

    try:
        refresh_token = get_refresh_token(client_id, client_secret)
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(refresh_token, encoding="utf-8")
        print(f"Refresh token saved to {OUTPUT_PATH}. Copy it to ANIMAI_YT_REFRESH_TOKEN in GitHub Secrets.")
        print("The token is not displayed in the terminal.")
    except Exception as error:
        print(f"OAuth failed ({type(error).__name__}); sensitive values were not printed.")
        sys.exit(1)
