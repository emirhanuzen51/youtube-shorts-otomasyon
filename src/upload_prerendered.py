"""
Pre-rendered video auto-uploader for YouTube Channels with Viral Growth Enhancements:
1. Auto Pinned/Engaging Comment (Drives comment section activity & algorithmic boost)
2. Dual-Language / Global Titles for Minik Maceralar (Unlocks international audience: US/EU/Global)
3. Previous Episode Linking (Looping binge-watch effect for serials)
4. Dynamic Viral Trend Hashtags & SEO Tag Enrichment
"""
import os
import sys
import json
import re
import glob
import subprocess
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.force-ssl"]
RELEASE_TAG = "videos-vault-v1"

HIKAYE_TOPICS = {
    1: ("Eski Çaydanlık ile İlk Ticaret", "Eski bir çaydanlığı 25 TL'ye kapatıp parlatıp satarak ilk kasayı katlama macerası başlıyor!"),
    2: ("Bit Pazarından Hurda Teyp", "Bit pazarında hurda teyp pazarlığı yapıp ucuza alarak kasayı büyütme peşindeler."),
    3: ("Şarjı Olmayan Eski Telefon", "Şarjı bile almayan eski tuşlu telefonu tamir edip satmak için pazarlık yapıyorlar."),
    4: ("Scooter ile Ulaşım Yatırımı", "Bu sefer hedeflerinde eski bir scooter var; al-sat yaparak sermayeyi katlamaya devam!"),
    5: ("Hurda Drone Yakaladık", "Pazarda gördükleri drone'u ucuza kapatıp karla satmak için çetin bir pazarlık dönüyor."),
    6: ("Hayata Küsmüş Bisiklet", "Eski, bakımsız bisikleti temizleyip elden geçirerek değer katıp satma planı."),
    7: ("Parayı Bulunca AVM ve Kıyafet", "İlk karlar geldikten sonra 6 bölümdür giydikleri pantolonu değiştirip AVM'ye alışverişe gidiyorlar!"),
    8: ("Kira Günü Geldi Çattı", "Kasada 3.600 TL birikmişken ev sahibi kapıya dayanıyor; kira mı ödenecek ticaret mi dönecek?"),
    9: ("Takipçilerin İsteğiyle Kuaför", "Yorumlarda saçlara takan izleyicilerin isteğiyle berbere gidip tarz yenileme günü."),
    10: ("Temiz Akıllı Telefon Pazarlığı", "Eski püskü mallardan sonra nihayet akıllı telefon ticaretine adım atıyorlar."),
    11: ("Telefonu Parlatıp İlana Koyduk", "Alınan akıllı telefonu temizleyip internete ilan vererek büyük kar hedefliyorlar."),
    12: ("Sabah Çayı ve Yeni Hedefler", "Sabah simit çay eşliğinde bir sonraki büyük al-sat hamlesini planlıyorlar."),
    13: ("Cide Memleket Havası ve Motor", "Memlekete gidip gezerken yolda kalmamak için motor kovalama macerası."),
    14: ("Aydın Didim Yolculuğu", "Memleket havasından sonra rotayı Aydın Didim'e çevirip tatil ve ticareti birleştiriyorlar."),
    15: ("Motoru Satıp Otobüse Talim", "Motoru güzel karla satıp yeni maceralar için otobüs yolculuğuna başlıyorlar."),
    16: ("Masa Sandalye Takımı Düştü", "Kafelerden düşen sağlam masa sandalye takımlarını toplayıp toplu satış peşindeler."),
    17: ("Hurdalar Arasında Hazine Avı", "Yine hurdacıları gezip gözlerine kestirdikleri antika ve parçaları topluyorlar."),
    18: ("4000 TL'lik Antika Avize", "Eski bir avizeyi ucuza kapatıp zenginlere satma planı ortalığı karıştırıyor."),
    19: ("Kasa Katlandı: 120.000 TL!", "Büyük ticaretler tutunca kasadaki para 120.000 TL barajını aşıyor!"),
    20: ("Orman Yollarında Macera", "Orman havası alalım derken arabayla bilmedikleri patikalarda heyecan dolu anlar."),
    21: ("Roket Gibi Satış: 200.000 TL", "Pazarcı gibi bağırıp çağırarak rekor satış yapıp kasayı 200 bine uçuruyorlar!"),
    22: ("Evdeki Bakırları Satınca Annem!", "Evdeki eski bakırları habersiz satmaya kalkınca anneden terlik yeme tehlikesi!"),
    23: ("Dededen Kalma Hurda Araba", "Dededen kalma eski arabayı 115 bine alıp sanayide toplayıp satma operasyonu."),
    24: ("300 Bine Bursa'dan Mercedes!", "Bursa'ya gidip 300 bin TL'ye efsane W124 kasa Mercedes kapıyorlar!"),
    25: ("E-Ticarete Girdik: Letgo ve Paketler", "Elektronik ürünleri internetten satmak için e-ticaret eğitimi ve paket alıyorlar."),
    26: ("Sanayide Turbo Masrafı ve Satış", "Aldıkları arabaya turbo yaptırıp 450 bine okutarak büyük vurgun yapıyorlar!"),
    28: ("Mercedes Çalındı mı?!", "Park ettikleri yerde Mercedes'i bulamayınca yaşanan büyük panik ve şok!"),
    30: ("Dubai'ye İndik Babalar!", "Kasa öyle bir katlandı ki soluğu çöllerin ve gökdelenlerin şehri Dubai'de alıyorlar!"),
    31: ("Dubai'de Traktör Mü Alınır?", "Dubai'ye gidip traktör ilanı kovalayan ortağa gelen çıldırma anları!"),
    32: ("Kaç Kerkenez Arkana Bakma!", "Dubai sokaklarında beklenmedik bir kovalamaca ve kaçış macerası."),
    34: ("Dükkandaki Malları Kapatıyoruz", "Batan bir dükkanın tüm mutfak ve cafe ekipmanlarını toptan kapatma hamlesi."),
    35: ("Mercedes Parçalandı: Büyük Yıkım", "Çalınan Mercedes'in parçalanmış iskeleti bulununca yaşanan hüzün ve yeniden başlangıç!"),
    36: ("Şile'ye ATV ile Yolculuk", "Yeni aldıkları ATV ile hem gezip tost yiyip hem de Şile'ye teslimata gidiyorlar."),
    37: ("Kerkenez Seyyar Köftecisi Kurduk!", "Köfte arabası alıp 'Kerkenez Köfte' tabelasını asarak sokak lezzetleri işine giriyorlar!")
}

BEBEK_TITLES = [
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

def extract_episode_num(filename: str) -> int:
    name = os.path.splitext(os.path.basename(filename))[0]
    matches = re.findall(r"(\d+)", name)
    return int(matches[-1]) if matches else 9999

def auto_listen_and_summarize(video_path: str, ep_num: int):
    temp_wav = os.path.join(os.path.dirname(video_path), f"temp_listen_{ep_num}.wav")
    try:
        cmd = f'ffmpeg -y -i "{video_path}" -vn -acodec pcm_s16le -ar 16000 -ac 1 "{temp_wav}"'
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if sr and os.path.exists(temp_wav):
            r = sr.Recognizer()
            with sr.AudioFile(temp_wav) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language="tr-TR")
            if os.path.exists(temp_wav):
                os.remove(temp_wav)
            first_sentence = text.split(".")[0] if "." in text else text[:80]
            topic = "Büyük Al-Sat Hamlesi"
            if any(w in text.lower() for w in ["araba", "mercedes", "araç", "motor", "sanayi"]):
                topic = "Yeni Araç Ticareti"
            elif any(w in text.lower() for w in ["para", "kasa", "bin", "milyon", "pazarlık"]):
                topic = "Büyük Pazarlık ve Kasa Katlama"
            elif any(w in text.lower() for w in ["uçak", "yol", "tatil", "gezi", "dubai"]):
                topic = "Yeni Şehir ve Yeni Fırsatlar"
            return topic, f"Kasa katlama serisinde yeni macera! Ekip bu bölümde: {first_sentence}..."
    except Exception as e:
        print(f"Otomatik dinleme notu: {e}")
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass
    return "Sıfırdan Zirveye Ticaret", "Kasa katlama serisinde heyecan ve yeni ticaret fırsatları hız kesmeden devam ediyor!"

def get_remote_assets():
    try:
        res = subprocess.run(["gh", "release", "view", RELEASE_TAG, "--json", "assets", "--jq", ".assets[].name"], capture_output=True, text=True)
        if res.returncode == 0:
            return set(res.stdout.split())
    except Exception:
        pass
    return set()

def download_video_from_vault(filename: str, dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    out_path = os.path.join(dest_dir, filename)
    if os.path.exists(out_path):
        return out_path
    print(f"GitHub Release Vault'tan indiriliyor: {filename}...")
    cmd = ["gh", "release", "download", RELEASE_TAG, "-p", filename, "-D", dest_dir, "--clobber"]
    ret = subprocess.run(cmd)
    if ret.returncode == 0 and os.path.exists(out_path):
        return out_path
    return None

def get_next_video(profile_key: str, folder: str, history_file: str):
    os.makedirs(os.path.dirname(os.path.abspath(history_file)), exist_ok=True)
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    uploaded_files = {item.get("filename") for item in history}
    
    local_videos = sorted(glob.glob(os.path.join(folder, "*.mp4")), key=extract_episode_num) if os.path.exists(folder) else []
    for v in local_videos:
        base = os.path.basename(v)
        if base not in uploaded_files:
            return v, history

    remote_assets = get_remote_assets()
    candidate_remotes = []
    for asset in remote_assets:
        if profile_key == "animai_studio" and re.search(r"^\d+\.mp4$", asset):
            candidate_remotes.append(asset)
        elif profile_key == "minik_maceralar" and (asset.startswith("leowildadventures-") or asset.startswith("mellofromars-") or not re.search(r"^\d+\.mp4$", asset)):
            candidate_remotes.append(asset)
            
    candidate_remotes = sorted(candidate_remotes, key=extract_episode_num)
    for asset in candidate_remotes:
        if asset not in uploaded_files:
            downloaded = download_video_from_vault(asset, folder)
            if downloaded:
                return downloaded, history

    return None, history

def build_metadata(profile_key: str, video_path: str, history: list):
    base = os.path.basename(video_path)
    upload_index = len(history)
    
    prev_link_text = ""
    if history:
        last_uploaded = history[-1]
        prev_link_text = f"⏮️ Önceki Bölüm: {last_uploaded.get('video_url', '')}\n"
        
    if profile_key == "animai_studio":
        ep_num = extract_episode_num(base)
        if ep_num in HIKAYE_TOPICS:
            topic, desc_plot = HIKAYE_TOPICS[ep_num]
        else:
            print(f"Yeni video tespit edildi ({base}), içeriği otomatik dinleniyor...")
            topic, desc_plot = auto_listen_and_summarize(video_path, ep_num)
        
        title = f"Kasa Katlama Bölüm {ep_num}: {topic} #Shorts"
        if len(title) > 100:
            title = title[:97] + "..."
            
        description = (
            f"🎬 Kasa Katlama Serisi - Bölüm {ep_num}: {topic}\n\n"
            f"📌 Bu Bölümde: {desc_plot}\n\n"
            f"{prev_link_text}"
            f"⏭️ Sonraki bölümleri kaçırmamak için Abone Olun & Bildirimleri Açın! 🔔\n\n"
            f"💬 Sizce bir sonraki bölümde hangi ürünü alıp satmalılar? Yorumlarda tahmininizi yazın! 👇\n\n"
            f"#AnimAIStudio #KasaKatlama #SıfırdanZengin #AlSat #Ticaret #KeşfetBeniÖneÇıkar #TrendShorts #AIAnimasyon #ViralShorts #3DAnimation #Shorts #YapayZeka"
        )
        tags = [
            "AnimAI Studio", "kasa katlama", f"kasa katlama bölüm {ep_num}", "sıfırdan zengin", 
            "al sat", "ticaret", "keşfet", "trend shorts", "shorts", "yapay zeka", "ai animasyon", 
            "3d animasyon", "hikaye", "animasyon", "viral shorts"
        ]
        pinned_comment = (
            f"🔥 Kasa Katlama Bölüm {ep_num} yayında!\n"
            f"Sizce bir sonraki bölümde kasayı neye basmalılar? En iyi tahmini sabitleyeceğim! 👇👇\n"
            f"🔔 Serinin devamı için abone olmayı unutmayın!"
        )
        category_id = "1"
        
    else:  # minik_maceralar
        title_idx = upload_index % len(BEBEK_TITLES)
        title = BEBEK_TITLES[title_idx]
        
        description = (
            f"Minik Maceralar dünyasından kalpleri eriten sıcacık bir an! 🍼✨\n"
            f"Welcome to tiny cute adventures! Sweetest moments to make your day! ❤️🐾\n\n"
            f"{prev_link_text}"
            f"🔔 Her gün yeni maceralar için ailemize katılın / Subscribe for daily cute shorts! 🥰\n\n"
            f"#MinikMaceralar #CuteBaby #BabyShorts #BabyAdventures #FunnyBaby #SevimliBebekler #BebekVideoları #TrendingShorts #ViralShorts #Shorts #Cute"
        )
        tags = [
            "Minik Maceralar", "cute baby", "baby shorts", "baby adventures", "funny baby",
            "sevimli bebekler", "bebek videoları", "tatlı bebek", "cute animals", "cute moments",
            "trending shorts", "viral shorts", "shorts", "for kids"
        ]
        pinned_comment = (
            f"Bu tatlılığa 10 üzerinden kaç verirsiniz? 🍼❤️ / Rate this cuteness from 1 to 10! 👇🥰\n"
            f"Her gün yeni videolar için abone olmayı unutmayın! 🔔"
        )
        category_id = "15"
        
    return title, description, tags, pinned_comment, category_id

def post_comment(youtube, video_id: str, comment_text: str):
    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
        res = youtube.commentThreads().insert(part="snippet", body=body).execute()
        print(f"BAŞARILI: Otomatik etkileşim yorumu eklendi! (Comment ID: {res.get('id')})")
    except Exception as e:
        print(f"Yorum ekleme notu: {e}")

def upload_prerendered_video(profile_key: str):
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    p_upper = profile_key.upper().replace('_', '')
    p_prefix = "ANIMAI" if "ANIMAI" in p_upper else p_upper
    client_id = os.environ.get(f"{p_prefix}_YT_CLIENT_ID") or os.environ.get(f"{p_upper}_YT_CLIENT_ID") or os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get(f"{p_prefix}_YT_CLIENT_SECRET") or os.environ.get(f"{p_upper}_YT_CLIENT_SECRET") or os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get(f"{p_prefix}_YT_REFRESH_TOKEN") or os.environ.get(f"{p_upper}_YT_REFRESH_TOKEN") or os.environ.get("YT_REFRESH_TOKEN")
    
    creds_file = os.path.join(root_dir, "channel_creds.json")
    if os.path.exists(creds_file) and not (client_id and client_secret and refresh_token):
        with open(creds_file, "r", encoding="utf-8") as f:
            all_creds = json.load(f)
            if profile_key in all_creds:
                p_c = all_creds[profile_key]
                client_id = p_c.get("client_id")
                client_secret = p_c.get("client_secret")
                refresh_token = p_c.get("refresh_token")

    if not (client_id and client_secret and refresh_token):
        raise ValueError(f"{profile_key} için YouTube kimlik bilgileri bulunamadı!")
        
    folder = os.path.join(root_dir, "Yeni klasör", "Hikaye_ai" if profile_key == "animai_studio" else "Bebek")
    history_file = os.path.join(root_dir, "data", f"history_{profile_key}.json")
    
    video_path, history = get_next_video(profile_key, folder, history_file)
    if not video_path:
        print(f"[{profile_key}] Yüklenecek yeni video kalmadı!")
        return None
        
    base = os.path.basename(video_path)
    title, description, tags, pinned_comment, category_id = build_metadata(profile_key, video_path, history)
    
    print(f"\n==========================================")
    print(f"Kanal: {profile_key}")
    print(f"Video Dosyası: {base}")
    print(f"Başlık: {title}")
    print(f"==========================================\n")
    
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    youtube = build("youtube", "v3", credentials=creds)
    
    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "tr",
            "defaultAudioLanguage": "tr"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Yükleme İlerlemesi: %{int(status.progress() * 100)}")
            
    video_id = response.get("id")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"\nBAŞARILI: Video yayınlandı! URL: {video_url}")
    
    post_comment(youtube, video_id, pinned_comment)
    
    history.append({
        "filename": base,
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "uploaded_at": datetime.now().isoformat()
    })
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    return video_url

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python upload_prerendered.py <animai_studio | minik_maceralar>")
        sys.exit(1)
    target = sys.argv[1].strip().lower()
    upload_prerendered_video(target)
