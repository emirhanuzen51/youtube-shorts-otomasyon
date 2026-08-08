"""One-time local script to obtain a YouTube OAuth refresh token.

Run this once on your own machine (NOT in CI):

    python setup/get_refresh_token.py

It opens a browser for you to sign in with the Google account that owns
your YouTube channel, then prints the refresh token to copy into your
GitHub repo secrets as YT_REFRESH_TOKEN (along with YT_CLIENT_ID and
YT_CLIENT_SECRET taken from client_secret.json).

Requires a `client_secret.json` (OAuth "Desktop app" client) downloaded
from Google Cloud Console, placed next to this script or in the project root.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube"]

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

    key = "installed" if "installed" in client_config else "web"
    client_id = client_config[key]["client_id"]
    client_secret = client_config[key]["client_secret"]

    print("\nSuccess! Add these as GitHub repo secrets:\n")
    print(f"YT_CLIENT_ID={client_id}")
    print(f"YT_CLIENT_SECRET={client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
