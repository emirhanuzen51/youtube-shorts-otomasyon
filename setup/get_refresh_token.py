"""One-time local script to obtain a YouTube OAuth refresh token.

Run this once on your own machine (NOT in CI):

    python setup/get_refresh_token.py

It opens a browser for you to sign in with the Google account that owns
your YouTube channel, then saves the refresh token to data/youtube_refresh_token.txt. The file is
gitignored; copy its contents into the matching GitHub repo secret, then remove
the local file.

Requires a `client_secret.json` (OAuth "Desktop app" client) downloaded
from Google Cloud Console, placed next to this script or in the project root.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

CANDIDATE_PATHS = [
    "client_secret.json",
    os.path.join(os.path.dirname(__file__), "client_secret.json"),
    os.path.join(os.path.dirname(__file__), "..", "client_secret.json"),
]


def find_client_secret():
    for path in CANDIDATE_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "client_secret.json not found. Download it from Google Cloud Console "
        "(APIs & Services > Credentials > OAuth client ID > Desktop app) and "
        "place it in the project root or setup/ folder."
    )


def main():
    client_secret_path = find_client_secret()
    with open(client_secret_path) as f:
        client_config = json.load(f)

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # Force Google to show account/channel selection again instead of silently
    # reusing a previously-granted (possibly wrong) channel.
    creds = flow.run_local_server(port=0, prompt="consent select_account")
    if not creds.refresh_token:
        raise RuntimeError("Google OAuth completed without returning a refresh token")

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "youtube_refresh_token.txt")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(creds.refresh_token)
    print(f"Refresh token saved to {os.path.abspath(output_path)}.")
    print("Copy it to the appropriate GitHub Secret, then remove the local file.")
    print("The token and OAuth client credentials are not displayed in the terminal.")


if __name__ == "__main__":
    main()
