"""Uploads pre-made video files as-is (no editing/re-encoding) to a channel,
with a generic title/description/tags template applied to all of them.

For channels like "Komedihanem" where the user supplies finished videos
directly (drop files into manual_uploads/<channel>/) instead of going
through the generate/render pipeline. Never modifies the video file itself -
only reads it for upload.

Usage:
    python upload_manual.py komedihanem

Credentials are read from YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN env
vars if set, otherwise from manual_uploads/<channel>/credentials.json (never
committed - see .gitignore).
"""
import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "manual_uploads")
VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi", ".webm")

# Generic template - deliberately not video-specific, applied to every
# upload in this channel's folder.
TEMPLATES = {
    "komedihanem": {
        "description": (
            "😂 Gülmek bulaşıcıdır!\n\n"
            "Kaçırmamak için abone ol, her gün yeni bir komedi anı için buradayız.\n\n"
            "#Komedi #Shorts #Mizah #Gülme #Espri"
        ),
        "tags": ["komedi", "mizah", "gulme", "espri", "eglence", "shorts", "komik video"],
        "category_id": "23",  # Comedy
        "title_prefix": "",
    },
}


def _credentials(channel: str) -> Credentials:
    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        cred_path = os.path.join(BASE_DIR, channel, "credentials.json")
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"No credentials in env vars and none found at {cred_path}. "
                "Run setup/get_refresh_token.py, then either export "
                "YT_CLIENT_ID/YT_CLIENT_SECRET/YT_REFRESH_TOKEN or save them "
                "as JSON ({\"client_id\":..,\"client_secret\":..,\"refresh_token\":..}) "
                f"to {cred_path}."
            )
        with open(cred_path, encoding="utf-8") as f:
            creds_data = json.load(f)
        client_id = creds_data["client_id"]
        client_secret = creds_data["client_secret"]
        refresh_token = creds_data["refresh_token"]

    return Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def _title_from_filename(filename: str, prefix: str) -> str:
    name = os.path.splitext(filename)[0]
    name = name.replace("_", " ").replace("-", " ").strip()
    name = " ".join(name.split())
    title = f"{prefix}{name}".strip() if name else "Komedi Anı"
    if len(title) > 100:
        title = title[:97] + "..."
    return title


def _load_log(log_path: str) -> dict:
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_log(log_path: str, log: dict):
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def upload_folder(channel: str):
    template = TEMPLATES[channel]
    folder = os.path.join(BASE_DIR, channel)
    os.makedirs(folder, exist_ok=True)
    log_path = os.path.join(folder, "uploaded.json")
    log = _load_log(log_path)

    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(VIDEO_EXTENSIONS) and f not in log
    )
    if not files:
        print("No new video files to upload.")
        return

    creds = _credentials(channel)
    youtube = build("youtube", "v3", credentials=creds)

    for filename in files:
        path = os.path.join(folder, filename)
        title = _title_from_filename(filename, template["title_prefix"])
        print(f"Uploading {filename!r} as {title!r}...")

        body = {
            "snippet": {
                "title": title,
                "description": template["description"],
                "tags": template["tags"],
                "categoryId": template["category_id"],
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            },
        }
        media = MediaFileUpload(path, mimetype="video/mp4", resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            _, response = request.next_chunk()

        video_id = response["id"]
        print(f"  Uploaded: https://youtube.com/shorts/{video_id}")
        log[filename] = video_id
        _save_log(log_path, log)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in TEMPLATES:
        print(f"Usage: python upload_manual.py <channel>  (choices: {list(TEMPLATES)})")
        sys.exit(1)
    upload_folder(sys.argv[1])
