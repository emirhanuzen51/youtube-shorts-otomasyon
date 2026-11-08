import json
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))

from src.prerendered_queue import canonical_asset_name
from src.upload_prerendered import SCOPES, upload_prerendered_video


PROFILE = "animai_studio"
EPISODE_THREE_ID = "2Y21bOSbukE"
EPISODE_FOUR_ID = "navUpIXaBoY"
EPISODE_THREE_FILE = "3.bolum.mp4"
HISTORY_FILE = os.path.join("data", "history_animai_studio.json")


def youtube_client():
    credentials = Credentials(
        token=None,
        refresh_token=os.environ["ANIMAI_YT_REFRESH_TOKEN"],
        client_id=os.environ["ANIMAI_YT_CLIENT_ID"],
        client_secret=os.environ["ANIMAI_YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=credentials)


def get_video(youtube, video_id):
    response = youtube.videos().list(part="status,snippet", id=video_id).execute()
    items = response.get("items", [])
    return items[0] if items else None


def load_history():
    with open(HISTORY_FILE, encoding="utf-8") as history_file:
        history = json.load(history_file)
    if not isinstance(history, list):
        raise ValueError(f"{HISTORY_FILE} must contain a JSON list")
    return history


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as history_file:
        json.dump(history, history_file, indent=2, ensure_ascii=False)
        history_file.write("\n")


def make_public(youtube, video):
    if video["status"].get("privacyStatus") == "public":
        return video["id"]
    youtube.videos().update(
        part="status",
        body={
            "id": video["id"],
            "status": {"privacyStatus": "public"},
        },
    ).execute()
    updated = get_video(youtube, video["id"])
    if not updated or updated["status"].get("privacyStatus") != "public":
        raise RuntimeError("Episode 3 could not be verified as public")
    return video["id"]


def publish_episode_three(youtube):
    video = get_video(youtube, EPISODE_THREE_ID)
    if video:
        print(f"Episode 3 already exists with privacy status {video['status'].get('privacyStatus')}.")
        return make_public(youtube, video)

    history = load_history()
    canonical_episode_three = canonical_asset_name(EPISODE_THREE_FILE)
    history = [
        item
        for item in history
        if item.get("video_id") != EPISODE_THREE_ID
        and canonical_asset_name(item.get("filename", "")) != canonical_episode_three
    ]
    save_history(history)
    upload_prerendered_video(PROFILE)

    history = load_history()
    candidates = [
        item
        for item in history
        if canonical_asset_name(item.get("filename", "")) == canonical_episode_three
        and item.get("video_id") != EPISODE_THREE_ID
    ]
    if not candidates:
        raise RuntimeError("Episode 3 upload did not create a history entry")
    video = get_video(youtube, candidates[-1]["video_id"])
    if not video or video["status"].get("privacyStatus") != "public":
        raise RuntimeError("Re-uploaded episode 3 could not be verified as public")
    return video["id"]


def delete_episode_four(youtube):
    video = get_video(youtube, EPISODE_FOUR_ID)
    if not video:
        print("Episode 4 is already absent from YouTube.")
        return
    youtube.videos().delete(id=EPISODE_FOUR_ID).execute()
    if get_video(youtube, EPISODE_FOUR_ID):
        raise RuntimeError("Episode 4 still exists after the delete request")
    print(f"Deleted episode 4 ({EPISODE_FOUR_ID}).")


def main():
    youtube = youtube_client()
    episode_three_id = publish_episode_three(youtube)
    print(f"Episode 3 is public: https://youtube.com/shorts/{episode_three_id}")
    delete_episode_four(youtube)


if __name__ == "__main__":
    main()
