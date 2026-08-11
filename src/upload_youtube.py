"""Uploads a rendered Short to YouTube via the YouTube Data API v3.

Auth uses a pre-obtained OAuth refresh token (see setup/get_refresh_token.py)
supplied through environment variables so this can run unattended in CI.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from profiles import get_profile

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]


def _get_credentials() -> Credentials:
    return Credentials(
        token=None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def build_title_description(question: dict, profile: dict):
    title = f"{question['question']} {profile['title_hashtags']}"
    if len(title) > 100:
        title = title[:97] + "..."

    answer_intro = profile.get("answer_intro", "Cevap:")
    comment_cta = profile.get("comment_cta", "Bu konuda ne düşünüyorsun? Yorumlarda paylaş 👇")
    dynamic_hashtags = " ".join(question.get("hashtags", []))
    hashtag_line = f"{profile['description_hashtags']} {dynamic_hashtags}".strip()
    description = (
        f"{question['question']}\n\n"
        f"{answer_intro} {question['answer']}\n"
        f"{question['explanation']}\n\n"
        f"{comment_cta}\n\n"
        f"{hashtag_line}"
    )
    tags = [*profile["tags"], question["category"], *[h.lstrip("#") for h in question.get("hashtags", [])]]
    return title, description, tags


def upload_video(video_path: str, question: dict, thumbnail_path: str | None = None, profile: dict | None = None) -> str:
    profile = profile or get_profile()
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    title, description, tags = build_title_description(question, profile)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()

    video_id = response["id"]
    print(f"Uploaded: https://youtube.com/shorts/{video_id}")

    comment_text = profile.get("comment_cta", "Bu konuda ne düşünüyorsun? Yorumlarda paylaş 👇")
    if comment_text:
        try:
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {"snippet": {"textOriginal": comment_text}},
                    }
                },
            ).execute()
            print("Posted the channel's own opening comment.")
        except Exception as e:
            # Pinning a comment isn't exposed by the Data API (Studio-only),
            # and comments could be disabled on a channel - never fail the
            # upload itself over this cosmetic extra step.
            print(f"Could not post opening comment: {e}")

    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("Thumbnail set from question scene.")
        except Exception as e:
            # YouTube currently doesn't support setting a custom thumbnail for
            # Shorts via the Data API (or desktop Studio) regardless of channel
            # verification - only the mobile app can do it. Never fail the
            # upload itself just because this cosmetic extra step is blocked.
            print(f"Could not set custom thumbnail (Shorts thumbnails are mobile-app-only on YouTube): {e}")

    return video_id


if __name__ == "__main__":
    import sys

    demo_question = {
        "category": "Türkiye coğrafyası",
        "question": "Türkiye'nin en yüksek dağı hangisidir?",
        "answer": "Ağrı Dağı",
        "explanation": "Ağrı Dağı, 5137 metre yüksekliğiyle Türkiye'nin en yüksek noktasıdır.",
    }
    upload_video(sys.argv[1], demo_question)
