"""One-off admin utility: deletes a single YouTube video by ID using the
same channel credentials (YT_CLIENT_ID/SECRET/REFRESH_TOKEN env vars) the
daily upload workflows already use. Run via the "Admin: Delete Video"
GitHub Actions workflow so no local OAuth re-auth is needed.
"""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]


def main():
    video_id = sys.argv[1]
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    youtube = build("youtube", "v3", credentials=creds)
    youtube.videos().delete(id=video_id).execute()
    print(f"Deleted video {video_id}")


if __name__ == "__main__":
    main()
