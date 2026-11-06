"""
Pre-rendered video auto-uploader for YouTube Channels with Viral Growth Enhancements:
1. Auto Pinned/Engaging Comment (Drives comment section activity & algorithmic boost)
2. Dual-Language / Global Titles for Minik Maceralar (Unlocks international audience: US/EU/Global)
3. Dynamic Viral Trend Hashtags & SEO Tag Enrichment
4. Comment Reply Bot (Increases engagement)
5. Optimal Upload Time Analysis (Maximizes views)
"""
import os
import sys
import json
import re
import glob
import random
import subprocess
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prerendered_queue import MAHALLE_RELEASE_ASSETS, canonical_asset_name, select_next_asset
from shorts_video import prepare_shorts_video

# Import optimization modules
try:
    from trending_hashtags import add_hashtags_to_description
    from comment_reply_bot import auto_reply_to_comments
    from optimal_upload_time import run_optimal_time_analysis
    OPTIMIZATION_ENABLED = True
except ImportError:
    OPTIMIZATION_ENABLED = False
    print("⚠️  Optimizasyon modülleri yüklenemedi, bazı özellikler devre dışı")

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

MAHALLE_TOPICS = {
    1: ("Ronaldo vs Messi İlk Maç", "10 yaşındaki Ronaldo ve Messi sokakta takım kuruyor! Ronaldo hile yapıp Neymar'ı alıyor, Messi Zidane'ı çağırıyor. Büyük rekabet başlıyor!"),
    2: ("Ronaldo'dan Füze Şut", "Ronaldo'dan füze gibi şut! Messi sinirlenip şova başlıyor. Kimse durduramıyor! Mbappe geliyor ve sadece gülüyor. Gol mü, direk mi?"),
    3: ("Zidane'dan Vole Gol", "Mbappe köşede izlerken maç devam ediyor. Neymar Messi'yi geçiyor, Ramos topu kazanıyor, Zidane inanılmaz vole golü atıyor! Sokak yıkılıyor!"),
    4: ("Takımlar Kuruluyor", "Mbappé maç teklifini kabul ediyor. Iniesta, Casillas ve Buffon gelmiyor. Ekipte 5 kişi: Ronaldo, Messi, Neymar, Zidane, Ramos. Neymar kuzenini çağırıyor. Son kişi kim?"),
    5: ("Ronaldinho Geliyor", "MAÇ GÜNÜ! Neymar kuzenini çağırıyor... RONALDINHO! Mbappé takımı savaş modunda! Haaland ortaya çıkıyor. Gizemli son oyuncu kim? Ronaldo'ya top öğreten çocuk kim?"),
    6: ("Haaland'dan Füze Gol", "Ronaldo, Messi, Neymar vs Mbappé! Ricardo Quaresma ortaya çıkıyor! Haaland gelişine vurdu! Dembélé'den mükemmel orta. Maç başladı!"),
    7: ("Savunma Yok", "Mbappé hızlandırıyor, Vinícius çalımlarla karıştırıyor. Dembélé tehlikeyi büyütüyor. Messi & Ronaldinho sahneye çıkıyor. Quaresma'dan EFSANE TRIVELA!"),
    8: ("Arda Güler Golü", "Arda Güler uzaktan golle maçı başlattı! Maldini oyuna dahil oldu. Mbappé takımı uzaktan şut stratejisi! Skor 5-2. Kaleci eksik! Geri dönüş mümkün mü?"),
    9: ("Buffon Refleksi", "Mbappé penaltısında Buffon'dan inanılmaz refleks! Ronaldo, Neymar ve Messi sahayı domine ediyor. Messi Antonela'yı görüyor. Messi'nin önünde ne yapacak?"),
    10: ("Messi Ankara Modu", "Messi Antonela'nın gelmesiyle Ankara modu açıyor! Golle takım oyuna dönüyor. Ronaldo müthiş frikik! Neymar inanılmaz gol! Skor 5-5! Mbappé: 'Atan kazanır!'"),
    11: ("Final Röveşata", "Son pozisyon! Orta açılıyor... RONALDO YÜKSELİYOR... RÖVEŞATAAAA!!! Maç bitiyor. Kazanan kim?"),
}

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
    21: ("Roket Gibi Satış: 200.000 TL", "Pazarcı gibi bağırıp çağırarak rekor satış yapıp kasayı 200 bine uçuruyorlar."),
    22: ("Evdeki Bakırları Satınca Annem!", "Evdeki eski bakırları habersiz satmaya kalkınca anneden terlik yeme tehlikesi!"),
    23: ("Dededen Kalma Hurda Araba", "Dededen kalma eski arabayı 115 bine alıp sanayide toplayıp satma operasyonu."),
    24: ("300 Bine Bursa'dan Mercedes!", "Bursa'ya gidip 300 bin TL'ye efsane W124 kasa Mercedes kapıyorlar!"),
    25: ("E-Ticarete Girdik: Letgo ve Paketler", "Elektronik ürünleri internetten satmak için e-ticaret eğitimi ve paket alıyorlar."),
    26: ("Sanayide Turbo Masrafı ve Satış", "Aldıkları arabaya turbo yaptırıp 450 bine okutarak büyük vurgun yapıyorlar."),
    28: ("Mercedes Çalındı mı?!", "Park ettikleri yerde Mercedes'i bulamayınca yaşanan büyük panik ve şok!"),
    30: ("Dubai'ye İndik Babalar!", "Kasa öyle bir katlandı ki soluğu çöllerin ve gökdelenlerin şehri Dubai'de alıyorlar."),
    31: ("Dubai'de Traktör Mü Alınır?", "Dubai'ye gidip traktör ilanı kovalayan ortağa gelen çıldırma anları!"),
    32: ("Kaç Kerkenez Arkana Bakma!", "Dubai sokaklarında beklenmedik bir kovalamaca ve kaçış macerası."),
    34: ("Dükkandaki Malları Kapatıyoruz", "Batan bir dükkanın tüm mutfak ve cafe ekipmanlarını toptan kapatma hamlesi."),
    35: ("Mercedes Parçalandı: Büyük Yıkım", "Çalınan Mercedes'in parçalanmış iskeleti bulununca yaşanan hüzün ve yeniden başlangıç!"),
    36: ("Şile'ye ATV ile Yolculuk", "Yeni aldıkları ATV ile hem gezip tost yiyip hem de Şile'ye teslimata gidiyorlar."),
    37: ("Kerkenez Seyyar Köftecisi Kurduk!", "Köfte arabası alıp 'Kerkenez Köfte' tabelasını asarak sokak lezzetleri işine giriyorlar!")
}

BEBEK_TITLES = [
    "Minik Maceralar: Öğren, Keşfet ve Eğlen! 🌈🎵 #Shorts",
    "Renkler, Sayılar ve Minik Keşifler! 🌈🔢 #Shorts",
    "Eğitici Şarkılar ve Eğlenceli Keşif Zamanı! 🎶🌿 #Shorts",
    "Minik Maceralar: Çocuklar İçin Eğlenceli Öğrenme! 🐾📚 #Shorts",
    "Şarkılarla ve Keşiflerle Öğreniyoruz! 🎵🌱 #Shorts",
]

def extract_episode_num(filename: str):
    name = os.path.splitext(os.path.basename(filename))[0]
    matches = re.findall(r"(\d+)", name)
    return int(matches[-1]) if matches else None


def is_mahalle_video(video_path: str) -> bool:
    basename = os.path.basename(video_path)
    return (
        "mahalle" in video_path.lower()
        or canonical_asset_name(basename) in MAHALLE_RELEASE_ASSETS
    )


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
    result = subprocess.run(
        ["gh", "release", "view", RELEASE_TAG, "--json", "assets", "--jq", ".assets[].name"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not list video vault assets: {result.stderr.strip()}")
    return set(result.stdout.split())

def download_video_from_vault(filename: str, dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    out_path = os.path.join(dest_dir, filename)
    if os.path.exists(out_path):
        return out_path
    print(f"GitHub Release Vault'tan indiriliyor: {filename}...")
    cmd = ["gh", "release", "download", RELEASE_TAG, "-p", filename, "-D", dest_dir, "--clobber"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode or not os.path.exists(out_path):
        raise RuntimeError(
            f"Could not download {filename} from the video vault: {result.stderr.strip()}"
        )
    return out_path

def get_next_video(profile_key: str, folder: str, history_file: str):
    os.makedirs(os.path.dirname(os.path.abspath(history_file)), exist_ok=True)
    if not os.path.isfile(history_file):
        raise FileNotFoundError(
            f"Upload history {history_file} is missing; refusing to risk a duplicate upload"
        )
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot read upload history {history_file}; refusing to risk a duplicate upload"
        ) from error
    if not isinstance(history, list):
        raise ValueError(f"Upload history {history_file} must contain a JSON list")
    if any(not isinstance(item, dict) or not isinstance(item.get("filename"), str) for item in history):
        raise ValueError(f"Upload history {history_file} contains an invalid entry")

    local_mahalle_assets = []
    if profile_key == "animai_studio":
        mahalle_folder = os.path.join(folder, "Mahalle_maçı")
        if os.path.isdir(mahalle_folder):
            local_mahalle_assets = glob.glob(os.path.join(mahalle_folder, "*.mp4"))

    local_minik_assets = []
    if profile_key == "minik_maceralar" and os.path.isdir(folder):
        local_minik_assets = glob.glob(os.path.join(folder, "*.mp4"))

    remote_assets = get_remote_assets()
    selected = select_next_asset(
        profile_key,
        local_mahalle_assets or local_minik_assets,
        remote_assets,
        history,
    )
    if selected is None:
        return None, history

    source, asset = selected
    if source == "local":
        return os.path.join(
            os.path.join(folder, "Mahalle_maçı") if profile_key == "animai_studio" else folder,
            asset,
        ), history
    return download_video_from_vault(asset, folder), history


def save_history(history: list, history_file: str):
    temp_path = f"{history_file}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    os.replace(temp_path, history_file)


def _is_mahalle_filename(filename: str) -> bool:
    return canonical_asset_name(filename) in MAHALLE_RELEASE_ASSETS


def _resolve_target_playlist(profile_key: str, video_path: str) -> str | None:
    base = os.path.basename(video_path)
    episode = extract_episode_num(base)
    is_mahalle = is_mahalle_video(video_path)
    is_kasa = (
        episode is not None
        and (episode in HIKAYE_TOPICS or re.fullmatch(r"\d+\.mp4", base) or "kasa" in base.lower())
    )

    if profile_key == "animai_studio" and is_mahalle:
        playlist_id = os.environ.get("MAHALLE_PLAYLIST_ID")
        if not playlist_id:
            raise ValueError("MAHALLE_PLAYLIST_ID is required before uploading a Mahalle Maçı video")
        return playlist_id
    if profile_key == "animai_studio" and is_kasa:
        return os.environ.get("ANIMAI_PLAYLIST_ID", "PLKdPAh8ARgHA")
    if profile_key == "minik_maceralar":
        return os.environ.get("MINIKMACERALAR_PLAYLIST_ID", "PLEiYrhkomZ2k")
    return None


def _video_is_in_playlist(youtube, playlist_id: str, video_id: str) -> bool:
    page_token = None
    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        for item in response.get("items", []):
            resource = item.get("snippet", {}).get("resourceId", {})
            if resource.get("videoId") == video_id:
                return True
        page_token = response.get("nextPageToken")
        if not page_token:
            return False


def repair_pending_playlist_items(youtube, profile_key: str, history: list, history_file: str):
    changed = False
    mahalle_playlist_id = os.environ.get("MAHALLE_PLAYLIST_ID")
    for item in history:
        filename = item.get("filename")
        if profile_key == "animai_studio" and _is_mahalle_filename(filename or ""):
            if not mahalle_playlist_id:
                raise ValueError("MAHALLE_PLAYLIST_ID is required to maintain the Mahalle Maçı playlist")
            if item.get("playlist_id") != mahalle_playlist_id:
                item["playlist_id"] = mahalle_playlist_id
                item["playlist_added"] = False
                changed = True
            elif "playlist_added" not in item:
                item["playlist_added"] = False
                changed = True
    if changed:
        save_history(history, history_file)

    for item in history:
        playlist_id = item.get("playlist_id")
        video_id = item.get("video_id")
        if not playlist_id or not video_id or item.get("playlist_added") is not False:
            continue
        if not _video_is_in_playlist(youtube, playlist_id, video_id):
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            ).execute()
        item["playlist_added"] = True
        save_history(history, history_file)
        print(f"Video {video_id} doğrulandı ve oynatma listesine ({playlist_id}) eklendi.")


def build_metadata(profile_key: str, video_path: str, history: list):
    base = os.path.basename(video_path)
    is_mahalle = is_mahalle_video(video_path)
        
    if profile_key == "animai_studio":
        ep_num = extract_episode_num(base)
        is_kasa_katlama = (ep_num is not None) and (ep_num in HIKAYE_TOPICS or re.match(r"^\d+\.mp4$", base) or "kasa" in base.lower())
        
        if is_mahalle:
            ep_disp = ep_num if ep_num is not None else 1
            if ep_disp in MAHALLE_TOPICS:
                topic, desc_plot = MAHALLE_TOPICS[ep_disp]
            else:
                print(f"Yeni Mahalle Maçı bölümü tespit edildi ({base}), içeriği otomatik dinleniyor...")
                topic, desc_plot = auto_listen_and_summarize(video_path, ep_disp)
            title = f"Mahalle Maçı Bölüm {ep_disp}: {topic} #Shorts"
            series_header = f"⚽ Mahalle Maçı Serisi - Bölüm {ep_disp}: {topic}"
            call_action = f"⚽ Mahalle Maçı Bölüm {ep_disp} yayında!\nSizce bir sonraki bölümde ne olacak? En iyi tahmini sabitleyeceğim! 👇👇"
            
            if len(title) > 100:
                title = title[:97] + "..."
                
            description = (
                f"{series_header}\n\n"
                f"📌 Bu Bölümde: {desc_plot}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⏭️ Sonraki bölümleri kaçırmamak için Abone Olun & Bildirimleri Açın! 🔔\n\n"
                f"💬 Sizce bir sonraki bölümde ne olacak? Yorumlarda tahmininizi yazın! 👇\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"#AnimAIStudio #MahalleMaçı #Futbol #Komik #MahalleMaçı #TrendShorts #ViralShorts #Shorts #Animasyon #Ronaldo #Messi #Neymar #Mbappe #Zidane #Ronaldinho #Haaland #ArdaGuler #Football #Soccer #FYP #Viral #Keşfet #MessiVsRonaldo #FutbolAnimasyon #SokakMaçı #ÇocukFutbol #FutbolEdit #FootballEdits #Gol #Şov"
            )
            tags = [
                "AnimAI Studio", "mahalle maçı", "futbol", "komik",
                "mahalle", "trend shorts", "shorts", "animasyon",
                "viral shorts", "mahalle maçları", "komik futbol",
                "ronaldo", "messi", "neymar", "mbappe", "zidane",
                "ronaldinho", "haaland", "arda güler", "football",
                "soccer", "fyp", "viral", "keşfet", "messivsronaldo",
                "futbol animasyon", "sokak maçı", "çocuk futbol",
                "futbol edit", "football edits", "gol", "şov"
            ]
            if ep_num is not None:
                tags.append(f"mahalle maçı bölüm {ep_num}")
            pinned_comment = (
                f"{call_action}\n"
                f"🔔 Yeni videoları kaçırmamak için abone olmayı unutmayın!"
            )
            category_id = "17"  # Sports category
            
        elif is_kasa_katlama:
            ep_disp = ep_num if ep_num is not None else 1
            if ep_disp in HIKAYE_TOPICS:
                topic, desc_plot = HIKAYE_TOPICS[ep_disp]
            else:
                print(f"Yeni video tespit edildi ({base}), içeriği otomatik dinleniyor...")
                topic, desc_plot = auto_listen_and_summarize(video_path, ep_disp)
            title = f"Kasa Katlama Bölüm {ep_disp}: {topic} #Shorts"
            series_header = f"🎬 Kasa Katlama Serisi - Bölüm {ep_disp}: {topic}"
            call_action = "🔥 Kasa Katlama Bölüm " + str(ep_disp) + " yayında!\nSizce bir sonraki bölümde kasayı neye basmalılar? En iyi tahmini sabitleyeceğim! 👇👇"
        else:
            print(f"Özel/Bağımsız video tespit edildi ({base}), içerik dinleniyor...")
            clean_name = os.path.splitext(base)[0].replace("_", " ").replace("-", " ").title()
            topic, desc_plot = auto_listen_and_summarize(video_path, 0)
            actual_topic = topic if topic != "Sıfırdan Zirveye Ticaret" else clean_name
            title = f"AnimAI Özel: {actual_topic} 🎬 #Shorts"
            series_header = f"🎬 AnimAI Özel Gösterim: {actual_topic}"
            call_action = "🔥 Yeni AnimAI macerası yayında!\nVideo hakkındaki düşüncelerinizi yorumlarda belirtin! 👇👇"
        
        if not is_mahalle:
            if len(title) > 100:
                title = title[:97] + "..."
                
            description = (
                f"{series_header}\n\n"
                f"📌 Bu Bölümde: {desc_plot}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"⏭️ Sonraki bölümleri kaçırmamak için Abone Olun & Bildirimleri Açın! 🔔\n\n"
                f"💬 Sizce bir sonraki bölümde hangi ürünü alıp satmalılar? Yorumlarda tahmininizi yazın! 👇\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"#AnimAIStudio #KasaKatlama #SıfırdanZengin #AlSat #Ticaret #KeşfetBeniÖneÇıkar #TrendShorts #AIAnimasyon #ViralShorts #3DAnimation #Shorts #YapayZeka"
            )
            tags = [
                "AnimAI Studio", "kasa katlama", "sıfırdan zengin", 
                "al sat", "ticaret", "keşfet", "trend shorts", "shorts", "yapay zeka", "ai animasyon", 
                "3d animasyon", "hikaye", "animasyon", "viral shorts"
            ]
            if ep_num is not None:
                tags.append(f"kasa katlama bölüm {ep_num}")
            pinned_comment = (
                f"{call_action}\n"
                f"🔔 Yeni videoları kaçırmamak için abone olmayı unutmayın!"
            )
            category_id = "1"
        
    else:  # minik_maceralar
        title = random.choice(BEBEK_TITLES)
        
        description = (
            f"Minik Maceralar'da renkleri, sayıları, bitkileri ve hayvanları keşfediyoruz; "
            f"çocuk şarkıları ve günlük minik keşiflerle eğlenerek öğreniyoruz! 🌈🔢🌿🐾🎵\n"
            f"Fun and educational Shorts for children: colors, numbers, plants, animals, "
            f"children's songs and little everyday discoveries!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔔 Yeni eğlenceli keşifler için abone olun! / Subscribe for more fun learning and songs! 🥰\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"#MinikMaceralar #Çocuklarİçin #EğiticiVideolar #Renkler #Sayılar #Bitkiler "
            f"#Hayvanlar #ÇocukŞarkıları #KidsLearning #Educational #KidsSongs #Shorts"
        )
        tags = [
            "Minik Maceralar", "çocuklar için", "eğitici videolar", "renkleri öğren",
            "sayıları öğren", "bitkiler", "hayvanlar", "çocuk şarkıları",
            "kids learning", "educational videos", "kids songs", "shorts",
        ]
        pinned_comment = ""
        category_id = "27"
        
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
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    youtube = build("youtube", "v3", credentials=creds)
    repair_pending_playlist_items(youtube, profile_key, history, history_file)
    if not video_path:
        print(f"[{profile_key}] Yüklenecek yeni video kalmadı!")
        return None
        
    base = os.path.basename(video_path)
    is_mahalle = is_mahalle_video(video_path)
    target_pl = _resolve_target_playlist(profile_key, video_path)
    upload_path = prepare_shorts_video(
        video_path,
        os.path.join(root_dir, "data", "shorts_converted", profile_key),
    )
    if upload_path != video_path:
        print(f"Yatay video Shorts formatına dönüştürüldü: {os.path.basename(upload_path)}")

    title, description, tags, pinned_comment, category_id = build_metadata(profile_key, video_path, history)

    # Add trending hashtags to description (skip for Mahalle Maçı - already has custom hashtags)
    if OPTIMIZATION_ENABLED and profile_key == "animai_studio" and not is_mahalle:
        description = add_hashtags_to_description(description, profile_key)
        print(f"✅ Trending hashtag'ler eklendi")
    
    print(f"\n==========================================")
    print(f"Kanal: {profile_key}")
    print(f"Video Dosyası: {base}")
    print(f"Başlık: {title}")
    print(f"==========================================\n")
    
    media = MediaFileUpload(upload_path, mimetype="video/mp4", resumable=True)
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
            "selfDeclaredMadeForKids": profile_key == "minik_maceralar"
        }
    }

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk(num_retries=5)
        if status:
            print(f"Yükleme İlerlemesi: %{int(status.progress() * 100)}")

    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube reported upload success without returning a video ID")
    video_url = f"https://youtube.com/shorts/{video_id}"
    print(f"\nBAŞARILI: Video yayınlandı! URL: {video_url}")
    
    history_entry = {
        "filename": base,
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "uploaded_at": datetime.now().isoformat(),
    }
    if target_pl:
        history_entry["playlist_id"] = target_pl
        history_entry["playlist_added"] = False
    history.append(history_entry)
    save_history(history, history_file)
    repair_pending_playlist_items(youtube, profile_key, history, history_file)

    if pinned_comment:
        post_comment(youtube, video_id, pinned_comment)
    
    # Start A/B test for title optimization
    # Auto-reply to recent comments
    if OPTIMIZATION_ENABLED and profile_key != "minik_maceralar":
        try:
            print(f"\n💬 Yorumlara otomatik cevap veriliyor...")
            auto_reply_to_comments(profile_key, video_id)
        except Exception as e:
            print(f"⚠️  Yorum cevaplama hatası: {e}")

    # Run optimal time analysis (weekly)
    if OPTIMIZATION_ENABLED:
        try:
            # Check if analysis was run in the last 7 days
            time_file = os.path.join(root_dir, "data", f"optimal_time_{profile_key}.json")
            should_analyze = True
            
            if os.path.exists(time_file):
                with open(time_file, "r", encoding="utf-8") as f:
                    time_data = json.load(f)
                last_update = datetime.fromisoformat(time_data["updated_at"])
                if (datetime.now() - last_update).days < 7:
                    should_analyze = False
            
            if should_analyze:
                print(f"\n⏰ En iyi saat analizi başlatılıyor...")
                run_optimal_time_analysis(profile_key, client_id, client_secret, refresh_token)
        except Exception as e:
            print(f"⚠️  Saat analizi hatası: {e}")
        
    return video_url

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python upload_prerendered.py <animai_studio | minik_maceralar>")
        sys.exit(1)
    target = sys.argv[1].strip().lower()
    upload_prerendered_video(target)
