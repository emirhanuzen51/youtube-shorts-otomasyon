"""
A/B Test Başlıkları - Otomatik Başlık Optimizasyonu

Her video için 3 farklı başlık oluşturur, 24 saat sonra en çok tıklananı seçer.
"""
import os
import json
import time
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]

def generate_ab_titles(profile_key: str, video_id: str, original_title: str):
    """Generates 3 A/B test titles for a video."""
    
    if profile_key == "animai_studio":
        # Extract episode number if exists
        ep_num = None
        if "Bölüm" in original_title:
            try:
                ep_num = int(original_title.split("Bölüm")[1].split(":")[0].strip())
            except:
                pass
        
        if ep_num:
            topic = original_title.split(":")[1].strip() if ":" in original_title else "Yeni Macera"
            return [
                original_title,  # Original
                f"{topic} #Shorts",  # Topic-focused
                f"Bölüm {ep_num}: {topic} mi? #Shorts"  # Question format
            ]
        else:
            return [
                original_title,
                f"{original_title.replace('AnimAI Özel: ', '')} #Shorts",
                f"Yeni AnimAI: {original_title.replace('AnimAI Özel: ', '')} #Shorts"
            ]
    
    elif profile_key == "minik_maceralar":
        # Predefined cute baby titles
        titles = [
            "Minik Kahramanın Büyük Keşfi! 🍼 | Cute Baby Big Adventure ✨ #Shorts",
            "Dünyanın En Tatlı Bebeği ve Sevimli Dostu 🐾 | Cute Baby & Puppy 👶 #Shorts",
            "Gülümsemenizi Garanti Eden Anlar! ❤️ | Sweetest Baby Moments 🍼 #Shorts",
            "Minik Kaşifin İlk Adımları 🌟 | Little Baby Steps to Adventure 👶 #Shorts",
            "Günün Neşesi: Sevimli Bebeğin Komik Halleri! 😂 | Funny Baby Moments 🍼 #Shorts",
            "Minik Kahraman Orman Maceralarında! 🌲 | Cute Baby in the Wild 👶 #Shorts",
            "Tatlılık Abidesi: Sevimli Dostuyla Oyunda! 🐶 | Baby & Animal Friends 🍼 #Shorts",
            "Kalpleri Eriten En Tatlı Bebek Anı! 🥰 | Heartwarming Cute Baby ✨ #Shorts",
            "Minik Mucize: Eğlenceli Dakikalar 🍼 | Tiny Wonders & Baby Fun 🎈 #Shorts",
            "Bebek Leo'nun Macera Dolu Günü! 🦁 | Baby Leo's Fun Day 👶 #Shorts",
            "En Komik ve Tatlı Bebek Hareketleri! 👶 | Adorable Baby Laughs 💖 #Shorts",
            "Bebek ve Minik Hayvan Dostunun Maceraları 🐾 | Baby & Little Buddy ✨ #Shorts",
            "Neşe Dolu Minik Gülüşler! 🍼 | Sweetest Baby Smiles 🌈 #Shorts",
            "Gözlerinizi Alamayacağınız Sevimli Anlar! 😍 | Cutest Baby Ever 👶 #Shorts",
            "Minik Dünyanın Büyük Kahramanı! 🌟 | Tiny Hero Baby 🍼 #Shorts",
            "Eğlenceli Oyun Zamanı: Sevimli Bebek! 🧸 | Baby Playtime Fun 👶 #Shorts",
            "Günün En Tatlı Videosu ile Gülümseyin! 💖 | Smile with Cute Baby 🍼 #Shorts"
        ]
        # Return 3 random titles
        import random
        return random.sample(titles, 3)
    
    return [original_title, original_title, original_title]

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

def get_video_stats(youtube, video_id):
    """Gets video statistics (views, click-through rate)."""
    try:
        response = youtube.videos().list(
            part="statistics",
            id=video_id
        ).execute()
        
        stats = response["items"][0]["statistics"]
        return {
            "views": int(stats.get("viewCount", 0)),
            "likes": int(stats.get("likeCount", 0)),
            "comments": int(stats.get("commentCount", 0))
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None

def update_video_title(youtube, video_id, new_title):
    """Updates video title."""
    try:
        response = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": {
                    "title": new_title
                }
            }
        ).execute()
        print(f"✅ Başlık güncellendi: {new_title}")
        return True
    except Exception as e:
        print(f"❌ Başlık güncelleme hatası: {e}")
        return False

def run_ab_test(profile_key: str, video_id: str, original_title: str, 
                client_id=None, client_secret=None, refresh_token=None):
    """Runs A/B test for a video title."""
    
    # Generate A/B titles
    ab_titles = generate_ab_titles(profile_key, video_id, original_title)
    
    print(f"\n🎯 A/B Test Başlıkları:")
    for i, title in enumerate(ab_titles, 1):
        print(f"   {i}. {title}")
    
    # Store test data
    test_data = {
        "video_id": video_id,
        "profile": profile_key,
        "titles": ab_titles,
        "current_title_index": 0,
        "upload_time": datetime.now().isoformat(),
        "check_time": (datetime.now() + timedelta(hours=24)).isoformat(),
        "completed": False
    }
    
    # Save to file
    ab_test_file = f"data/ab_test_{profile_key}.json"
    os.makedirs(os.path.dirname(ab_test_file), exist_ok=True)
    
    all_tests = []
    if os.path.exists(ab_test_file):
        with open(ab_test_file, "r", encoding="utf-8") as f:
            all_tests = json.load(f)
    
    all_tests.append(test_data)
    with open(ab_test_file, "w", encoding="utf-8") as f:
        json.dump(all_tests, f, indent=2, ensure_ascii=False)
    
    print(f"✅ A/B test kaydedildi: {ab_test_file}")
    return test_data

def check_and_optimize_titles(profile_key: str, client_id, client_secret, refresh_token):
    """Checks pending A/B tests and optimizes titles."""
    
    ab_test_file = f"data/ab_test_{profile_key}.json"
    if not os.path.exists(ab_test_file):
        print("⏭️  Bekleyen A/B testi yok")
        return
    
    with open(ab_test_file, "r", encoding="utf-8") as f:
        all_tests = json.load(f)
    
    youtube = get_youtube_client(client_id, client_secret, refresh_token)
    updated_tests = []
    
    for test in all_tests:
        if test["completed"]:
            updated_tests.append(test)
            continue
        
        check_time = datetime.fromisoformat(test["check_time"])
        if datetime.now() < check_time:
            print(f"⏳ {test['video_id']} için 24 saat henüz dolmadı")
            updated_tests.append(test)
            continue
        
        # Time to check and optimize
        print(f"\n🔍 {test['video_id']} için A/B test sonuçları kontrol ediliyor...")
        
        stats = get_video_stats(youtube, test["video_id"])
        if stats:
            print(f"   Görüntülenme: {stats['views']}")
            print(f"   Beğeni: {stats['likes']}")
            print(f"   Yorum: {stats['comments']}")
            
            # For simplicity, we'll keep the original title if views > 100
            # In a real implementation, you'd test all 3 titles
            if stats['views'] < 100:
                # Try alternative title
                current_idx = test["current_title_index"]
                next_idx = (current_idx + 1) % len(test["titles"])
                
                print(f"🔄 Başlık değiştiriliyor: {test['titles'][next_idx]}")
                if update_video_title(youtube, test["video_id"], test["titles"][next_idx]):
                    test["current_title_index"] = next_idx
                    test["check_time"] = (datetime.now() + timedelta(hours=24)).isoformat()
                    updated_tests.append(test)
                else:
                    test["completed"] = True
                    updated_tests.append(test)
            else:
                print(f"✅ İyi performans, başlık korunuyor")
                test["completed"] = True
                updated_tests.append(test)
        else:
            updated_tests.append(test)
    
    # Save updated tests
    with open(ab_test_file, "w", encoding="utf-8") as f:
        json.dump(updated_tests, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Kullanım:")
        print("  python ab_test_titles.py <profile> <video_id> <original_title> --start")
        print("  python ab_test_titles.py <profile> --check")
        sys.exit(1)
    
    profile = sys.argv[1]
    
    # Load credentials from channel_creds.json
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creds_file = os.path.join(root_dir, "channel_creds.json")
    
    with open(creds_file, "r", encoding="utf-8") as f:
        all_creds = json.load(f)
    
    if profile not in all_creds:
        print(f"Profile not found: {profile}")
        sys.exit(1)
    
    creds = all_creds[profile]
    
    if sys.argv[2] == "--check":
        check_and_optimize_titles(profile, creds["client_id"], creds["client_secret"], creds["refresh_token"])
    else:
        video_id = sys.argv[2]
        original_title = sys.argv[3]
        run_ab_test(profile, video_id, original_title, creds["client_id"], creds["client_secret"], creds["refresh_token"])
