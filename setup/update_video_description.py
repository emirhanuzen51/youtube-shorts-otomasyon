#!/usr/bin/env python3
"""YouTube video açıklamasını güncelleme scripti"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

def update_video_description(video_id: str, new_description: str):
    """Video açıklamasını güncelle"""
    
    # Get credentials from environment variables
    client_id = os.environ.get("ANIMAI_YT_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("ANIMAI_YT_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("ANIMAI_YT_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
    
    if not (client_id and client_secret and refresh_token):
        print("❌ YouTube kimlik bilgileri bulunamadı!")
        print("Environment variables olarak şunları set et:")
        print("  ANIMAI_YT_CLIENT_ID")
        print("  ANIMAI_YT_CLIENT_SECRET")
        print("  ANIMAI_YT_REFRESH_TOKEN")
        return False
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    
    youtube = build("youtube", "v3", credentials=creds)
    
    try:
        # Get current video info
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()
        
        if not video_response.get("items"):
            print(f"❌ Video bulunamadı: {video_id}")
            return False
        
        snippet = video_response["items"][0]["snippet"]
        
        # Update description
        snippet["description"] = new_description
        
        # Update video
        update_response = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": snippet
            }
        ).execute()
        
        print(f"✅ Video açıklaması güncellendi: {video_id}")
        return True
        
    except HttpError as e:
        print(f"❌ YouTube API hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Kullanım:")
        print("  python update_video_description.py <video_id> <description>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    description = sys.argv[2]
    
    update_video_description(video_id, description)
