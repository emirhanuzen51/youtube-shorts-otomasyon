"""
En İyi Saat Analizi

YouTube Data API ile kanalınızın en çok izlendiği saati bulur
ve upload saatini otomatik ayarlar.
"""
import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

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

def get_channel_videos(youtube, days: int = 30):
    """Gets videos from the last N days."""
    try:
        # Calculate date range
        published_after = (datetime.now() - timedelta(days=days)).isoformat() + "Z"
        
        response = youtube.search().list(
            part="snippet",
            order="date",
            type="video",
            publishedAfter=published_after,
            maxResults=50
        ).execute()
        
        videos = []
        for item in response.get("items", []):
            videos.append({
                "id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"]
            })
        
        return videos
    except Exception as e:
        print(f"Error getting videos: {e}")
        return []

def get_video_stats(youtube, video_id: str):
    """Gets video statistics."""
    try:
        response = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        ).execute()
        
        if response.get("items"):
            item = response["items"][0]
            return {
                "views": int(item["statistics"].get("viewCount", 0)),
                "likes": int(item["statistics"].get("likeCount", 0)),
                "comments": int(item["statistics"].get("commentCount", 0)),
                "published_at": item["snippet"]["publishedAt"]
            }
    except Exception as e:
        print(f"Error getting stats: {e}")
    
    return None

def analyze_upload_times(videos: list, youtube):
    """Analyzes upload times and their performance."""
    
    upload_hour_stats = {}
    
    for video in videos:
        stats = get_video_stats(youtube, video["id"])
        if stats:
            # Parse publish time and extract hour (UTC)
            publish_time = datetime.fromisoformat(stats["published_at"].replace("Z", "+00:00"))
            hour_utc = publish_time.hour
            views = stats["views"]
            
            if hour_utc not in upload_hour_stats:
                upload_hour_stats[hour_utc] = {"total_views": 0, "count": 0}
            
            upload_hour_stats[hour_utc]["total_views"] += views
            upload_hour_stats[hour_utc]["count"] += 1
    
    # Calculate average views per hour
    hour_avg = {}
    for hour, stats in upload_hour_stats.items():
        if stats["count"] > 0:
            hour_avg[hour] = stats["total_views"] / stats["count"]
    
    return hour_avg

def convert_to_turkish_time(utc_hour: int):
    """Converts UTC hour to Turkey time (UTC+3)."""
    tr_hour = (utc_hour + 3) % 24
    return tr_hour

def save_optimal_time(profile_key: str, optimal_hour: int, avg_views: float):
    """Saves the optimal upload time."""
    time_file = f"data/optimal_time_{profile_key}.json"
    os.makedirs(os.path.dirname(time_file), exist_ok=True)
    
    time_data = {
        "optimal_hour_utc": optimal_hour,
        "optimal_hour_tr": convert_to_turkish_time(optimal_hour),
        "avg_views": avg_views,
        "updated_at": datetime.now().isoformat()
    }
    
    with open(time_file, "w", encoding="utf-8") as f:
        json.dump(time_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ En iyi saat kaydedildi: {time_file}")
    return time_data

def get_optimal_time(profile_key: str):
    """Gets the saved optimal upload time."""
    time_file = f"data/optimal_time_{profile_key}.json"
    
    if os.path.exists(time_file):
        with open(time_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return None

def run_optimal_time_analysis(profile_key: str, client_id=None, client_secret=None, refresh_token=None):
    """Runs optimal time analysis for a profile."""
    
    print(f"\n🔍 {profile_key} için en iyi saat analizi başlatılıyor...")
    
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
    
    # Get YouTube client
    youtube = get_youtube_client(client_id, client_secret, refresh_token)
    
    # Get recent videos
    videos = get_channel_videos(youtube, days=30)
    
    if not videos:
        print("⏭️  Son 30 günde video bulunamadı")
        return
    
    print(f"📊 {len(videos)} video analiz ediliyor...")
    
    # Analyze upload times
    hour_avg = analyze_upload_times(videos, youtube)
    
    if hour_avg:
        # Find best hour
        best_hour_utc = max(hour_avg.items(), key=lambda x: x[1])
        best_hour_tr = convert_to_turkish_time(best_hour_utc[0])
        
        print(f"\n🎯 En İyi Upload Saati:")
        print(f"   UTC: {best_hour_utc[0]}:00")
        print(f"   Türkiye: {best_hour_tr}:00")
        print(f"   Ortalama Görüntülenme: {best_hour_utc[1]:.0f}")
        
        print(f"\n📊 Saatlere Göre Performans:")
        for hour in sorted(hour_avg.keys()):
            tr_hour = convert_to_turkish_time(hour)
            print(f"   {tr_hour:02d}:00 - {hour_avg[hour]:.0f} avg views")
        
        # Save optimal time
        time_data = save_optimal_time(profile_key, best_hour_utc[0], best_hour_utc[1])
        
        return time_data
    else:
        print("❌ Yeterli veri bulunamadı")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Kullanım:")
        print("  python optimal_upload_time.py <profile>")
        print("  python optimal_upload_time.py <profile> --get")
        sys.exit(1)
    
    profile = sys.argv[1]
    
    # Load credentials from channel_creds.json
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creds_file = os.path.join(root_dir, "channel_creds.json")
    
    with open(creds_file, "r", encoding="utf-8") as f:
        all_creds = json.load(f)
    
    if profile not in all_creds:
        print(f"Profile not found: {profile}")
        sys.exit(1)
    
    creds = all_creds[profile]
    
    if len(sys.argv) > 2 and sys.argv[2] == "--get":
        # Get saved optimal time
        time_data = get_optimal_time(profile)
        if time_data:
            print(f"🎯 Kaydedilen En İyi Saat:")
            print(f"   UTC: {time_data['optimal_hour_utc']}:00")
            print(f"   Türkiye: {time_data['optimal_hour_tr']}:00")
            print(f"   Ortalama Görüntülenme: {time_data['avg_views']:.0f}")
            print(f"   Güncelleme Tarihi: {time_data['updated_at']}")
        else:
            print("⏭️  Kaydedilen saat bulunamadı. Analiz çalıştırın.")
    else:
        # Run analysis
        run_optimal_time_analysis(profile, creds["client_id"], creds["client_secret"], creds["refresh_token"])
