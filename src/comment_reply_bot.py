"""
Comment Reply Bot

Her videoya gelen ilk 5 yorumu otomatik cevaplar.
"""
import os
import json
import random
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

# Predefined reply templates
REPLY_TEMPLATES = {
    "animai_studio": [
        "Teşekkürler! Sizce bir sonraki bölümde kasayı neye basmalılar? En iyi tahmini sabitleyeceğim! 👇",
        "Harika yorum! Kasa katlama macerası devam ediyor. Sizce hangi ürünü alıp satmalılar? 💰",
        "İzlediğiniz için teşekkürler! Bir sonraki bölümde neler olacak merak mı ediyorsunuz? 🤔",
        "Süper! Sizce bu ticaret karlı mı oldu? Yorumlarda paylaşın! 🎯",
        "Abone olduğunuz için teşekkürler! Sizce kasa ne zaman 1 milyona ulaşacak? 💵"
    ],
    "minik_maceralar": [
        "Çok tatlı! ❤️ Daha fazla macera için abone olmayı unutmayın! 🔔",
        "Neşeniz bize yetti! 😊 Her gün yeni maceralar için takipte kalın! 🍼",
        "İzlediğiniz için teşekkürler! Bu tatlılığa kaç verirsiniz? 1-10 arası yazın! 🌟",
        "Sevimli değil mi? 😍 Daha fazlası için abone butonuna basmayı unutmayın! 👶",
        "Gülümsemeye devam edin! Her gün yeni videolar geliyor! 🎈"
    ]
}

def get_youtube_client(client_id, client_secret, refresh_token):
    """Creates YouTube API client."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("youtube", "v3", credentials=creds)

def get_video_comments(youtube, video_id, max_results: int = 5):
    """Gets recent comments for a video."""
    try:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_results,
            order="time"
        ).execute()
        
        comments = []
        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "id": item["id"],
                "author": comment["authorDisplayName"],
                "authorChannelId": comment.get("authorChannelId", {}).get("value", ""),
                "text": comment["textDisplay"],
                "published_at": comment["publishedAt"]
            })
        
        return comments
    except Exception as e:
        print(f"Error getting comments: {e}")
        return []

def reply_to_comment(youtube, comment_id: str, reply_text: str):
    """Replies to a comment."""
    try:
        response = youtube.comments().insert(
            part="snippet",
            body={
                "snippet": {
                    "parentId": comment_id,
                    "textOriginal": reply_text
                }
            }
        ).execute()
        print(f"✅ Yorum cevaplandı: {reply_text[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Yorum cevaplama hatası: {e}")
        return False

def get_replied_comments(profile_key: str):
    """Gets list of already replied comment IDs."""
    reply_file = f"data/replied_comments_{profile_key}.json"
    os.makedirs(os.path.dirname(reply_file), exist_ok=True)
    
    if os.path.exists(reply_file):
        with open(reply_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return []

def save_replied_comment(profile_key: str, comment_id: str):
    """Saves a replied comment ID."""
    reply_file = f"data/replied_comments_{profile_key}.json"
    
    replied = get_replied_comments(profile_key)
    replied.append(comment_id)
    
    with open(reply_file, "w", encoding="utf-8") as f:
        json.dump(replied, f, indent=2, ensure_ascii=False)

def auto_reply_to_comments(profile_key: str, video_id: str, client_id=None, client_secret=None, refresh_token=None):
    """Automatically replies to recent comments."""
    
    # Load credentials from channel_creds.json if not provided
    if not (client_id and client_secret and refresh_token):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_file = os.path.join(root_dir, "channel_creds.json")
        
        with open(creds_file, "r", encoding="utf-8") as f:
            all_creds = json.load(f)
        
        if profile_key not in all_creds:
            print(f"Profile not found: {profile_key}")
            return
        
        creds = all_creds[profile_key]
        client_id = creds["client_id"]
        client_secret = creds["client_secret"]
        refresh_token = creds["refresh_token"]
    
    youtube = get_youtube_client(client_id, client_secret, refresh_token)
    
    # Get recent comments
    comments = get_video_comments(youtube, video_id, max_results=10)
    
    if not comments:
        print("⏭️  Yorum bulunamadı")
        return
    
    # Get already replied comments
    replied = get_replied_comments(profile_key)
    
    # Get reply templates
    templates = REPLY_TEMPLATES.get(profile_key, REPLY_TEMPLATES["animai_studio"])
    
    print(f"\n💬 {len(comments)} yorum bulundu")
    
    # Get channel ID to skip own comments
    try:
        channel_response = youtube.channels().list(part="id", mine=True).execute()
        channel_id = channel_response["items"][0]["id"]
    except:
        channel_id = None
    
    for comment in comments:
        if comment["id"] in replied:
            print(f"⏭️  Zaten cevaplandı: {comment['author']}")
            continue
        
        # Skip own comments (the pinned comment we posted)
        if channel_id and comment.get("authorChannelId") == channel_id:
            print(f"⏭️  Kendi yorumu atlandı: {comment['author']}")
            continue
        
        # Select random reply
        reply_text = random.choice(templates)
        
        # Reply
        if reply_to_comment(youtube, comment["id"], reply_text):
            save_replied_comment(profile_key, comment["id"])
            print(f"   {comment['author']}: {comment['text'][:30]}...")
        else:
            continue

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  python comment_reply_bot.py <profile> <video_id>")
        sys.exit(1)
    
    profile = sys.argv[1]
    video_id = sys.argv[2]
    
    # Load credentials from channel_creds.json
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creds_file = os.path.join(root_dir, "channel_creds.json")
    
    with open(creds_file, "r", encoding="utf-8") as f:
        all_creds = json.load(f)
    
    if profile not in all_creds:
        print(f"Profile not found: {profile}")
        sys.exit(1)
    
    creds = all_creds[profile]
    
    auto_reply_to_comments(profile, video_id, creds["client_id"], creds["client_secret"], creds["refresh_token"])
