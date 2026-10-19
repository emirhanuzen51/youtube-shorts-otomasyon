# Otonom YouTube Shorts Otomasyonu — Uçtan Uca Kurulum Rehberi

Bu doküman, Gemini + edge-tts + MoviePy + YouTube Data API v3 + GitHub Actions
kullanan, **tamamen ücretsiz** araçlarla çalışan, günlük olarak kendiliğinden
soru üretip Türkçe seslendirip video render edip YouTube Shorts'a yükleyen bir
otomasyon sisteminin tam teknik özetidir. Zaten çalışan, gerçek bir sistemin
dokümantasyonudur (5 farklı kanalda test edilmiştir: KPSS, Ehliyet, Tarihte
Bugün, Ülke-Başkent, İngilizce Kelime).

## Bu dokümanı bir AI'ya (Claude Code, Cursor, ChatGPT + kod yazma vb.) verirsen

AI'nın yapması gerekenler (tamamen otomatik yapılabilir):
- Aşağıdaki dosya yapısını ve kodun BİREBİR aynısını oluşturmak (kod tam aşağıda,
  değiştirmeden kopyalanabilir; sadece "Yeni bir kanal eklemek" bölümündeki gibi
  profil eklerken içerik/marka metinleri özelleştirilir)
- `pip install -r requirements.txt` çalıştırmak, lokal test etmek
- git repo init/commit/push yapmak
- `gh` CLI kuruluysa GitHub secret'larını komutla eklemek

Kullanıcının (insanın) yapması gerekenler (AI bunları YAPAMAZ, tarayıcı erişimi
gerektirir — AI sadece talimat verip sonucu doğrulayabilir):
- Google Cloud Console'da proje/OAuth kurulumu
- YouTube kanalı oluşturmak
- OAuth izin ekranında Google hesabıyla giriş yapıp "İzin ver" demek
- GitHub'da repo oluşturmak (veya `gh repo create` ile AI yapabilir, credential varsa)
- Profil resmini YouTube Studio'ya manuel yüklemek (API bunu desteklemiyor)

Aşağıdaki "Kurulum Adımları" bölümü, insan + AI'nın birlikte hangi sırayla
ilerleyeceğini adım adım anlatır. Sistemin kod mimarisi tamamen bu dokümanın
içinde, kopyala-yapıştır seviyesinde eksiksiz verilmiştir.

---

## 1. Sistem Ne Yapar

Her gün, belirlenen bir saatte (GitHub Actions cron ile), her kanal için:

1. **Soru üretimi**: Gemini API (ücretsiz tier) ile o kanalın konusuna uygun,
   özgün bir Türkçe soru + cevap + açıklama üretilir. Daha önce sorulmuş
   sorularla tekrar etmemesi için son 50 soru prompt'a "bunları tekrarlama"
   diye eklenir.
2. **Seslendirme**: edge-tts (Microsoft'un ücretsiz, API-key gerektirmeyen
   TTS kütüphanesi) ile soru ve cevap Türkçe kadın sesiyle (`tr-TR-EmelNeural`)
   seslendirilir.
3. **Video render**: PIL (Pillow) ile kare kare çizilen, MoviePy ile mp4'e
   dönüştürülen 1080x1920 (Shorts formatı) bir video üretilir. Stok görsel/
   video kullanılmaz — arka plan, kod ile üretilen canlı bir gradyan animasyon.
   Sahneler: intro (kategori rozeti) → soru göster → geri sayım (4 sn) →
   cevap reveal (yeşil ekran) + açıklama → outro ("Takip et" çağrısı).
4. **YouTube'a yükleme**: YouTube Data API v3 ile, önceden alınmış bir OAuth
   refresh token kullanılarak video herkese açık olarak yüklenir. Başlık,
   açıklama, etiketler kanalın profiline göre otomatik oluşturulur.
5. **Geçmiş kaydı**: Üretilen soru, o kanalın `history_*.json` dosyasına
   eklenir ve GitHub'a commit'lenir (tekrar önleme + arşiv için).

Tüm bunlar GitHub Actions runner'ında (ubuntu-latest, ücretsiz) çalışır —
kullanıcının bilgisayarı kapalı olsa da, internet bağlantısı olmasa da sistem
çalışmaya devam eder.

### Neden ücretsiz kalıyor
- **Gemini API**: ücretsiz tier'da günlük istek limiti var ama 1 kanal 1
  video/gün için fazlasıyla yeterli.
- **edge-tts**: tamamen ücretsiz, API key gerektirmiyor (Microsoft Edge'in
  genel kullanıma açık TTS servisini kullanıyor).
- **GitHub Actions**: public/private repo'larda aylık ücretsiz dakika kotası
  var, bu iş günde ~3-5 dakika sürüyor, kotaya rahatça sığar.
- **YouTube Data API v3**: günlük 10.000 birim ücretsiz kota; bir video
  yükleme ~1600 birim, günde birkaç video için fazlasıyla yeterli.

---

## 2. Mimari ve Dosya Yapısı

```
proje-klasoru/
├── .github/workflows/
│   ├── daily_short_kpss.yml          # her kanal için ayrı workflow dosyası
│   ├── daily_short_ehliyet.yml
│   └── ...
├── assets/
│   ├── fonts/
│   │   ├── Anton-Regular.ttf         # Google Fonts, OFL lisanslı, ücretsiz
│   │   └── OFL.txt
│   └── music/                        # opsiyonel, boşsa müziksiz render eder
├── data/
│   ├── history_kpss.json             # her kanal için ayrı geçmiş dosyası
│   └── ...
├── setup/
│   ├── get_refresh_token.py          # tek seferlik OAuth script'i (lokal çalıştırılır)
│   └── channel_branding.py           # banner/profil resmi/açıklama üretip gönderir
├── src/
│   ├── profiles.py                   # TÜM kanalların konfigürasyonu burada
│   ├── generate_question.py          # Gemini ile soru üretimi
│   ├── tts.py                        # edge-tts seslendirme
│   ├── render_video.py               # PIL + MoviePy video render
│   ├── text_sanitize.py              # LLM çıktısını temizleme (özel karakter/emoji)
│   ├── upload_youtube.py             # YouTube Data API v3 yükleme
│   └── main.py                       # orkestrasyon: hepsini sırayla çalıştırır
├── client_secret.json                # OAuth Desktop client (GİTİGNORE'DA, asla commit'lenmez)
├── requirements.txt
└── .gitignore
```

**Anahtar tasarım kararı — "profil" sistemi**: Tüm kanallar AYNI kodu paylaşır.
Hangi kanal için çalışacağı `CONTENT_PROFILE` ortam değişkeniyle seçilir
(`src/profiles.py` içindeki bir dict key'i). Yeni bir kanal eklemek = 
`profiles.py`'a yeni bir dict girişi eklemek + yeni bir workflow dosyası
kopyalamak. Render, TTS, upload kodunun HİÇBİRİNE dokunulmaz.

---

## 3. Tam Kaynak Kodu

Aşağıdaki tüm dosyalar birebir, eksiksiz ve çalışır durumdadır. Sırayla
oluşturulmalıdır.

### `requirements.txt`

```txt
google-genai>=1.0
edge-tts>=6.1
moviepy>=2.1
pillow>=10.0
numpy>=1.26
fonttools>=4.53
google-api-python-client>=2.140
google-auth>=2.34
google-auth-oauthlib>=1.2
```

### `.gitignore`

```gitignore
__pycache__/
*.pyc
.env
client_secret.json
token.json
output/
*.mp4
*.mp3
!assets/music/*.mp3
venv/
.venv/
```

### `src/profiles.py`

Bu dosya sistemin kalbi. Her yeni kanal buraya bir dict olarak eklenir.

```python
"""Per-channel content configuration. Add a new dict here to spin up another
exam-prep channel on the same codebase - everything else (TTS, rendering,
upload, scheduling) is shared.
"""
import os

PROFILES = {
    "kpss": {
        "categories": [
            "Türkiye tarihi", "dünya tarihi", "Türkiye coğrafyası", "dünya coğrafyası",
            "vatandaşlık ve anayasa", "güncel bilgiler", "genel kültür", "sanat ve edebiyat",
            "bilim ve teknoloji", "Atatürk ilkeleri ve inkılap tarihi",
        ],
        "topic_label": "KPSS Genel Kültür sınavı",
        "history_file": "history_kpss.json",
        "video_badge": "KPSS SORUSU",
        "guess_prompt": "Cevabı biliyor musun?",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni soru!",
        "title_hashtags": "#Shorts #KPSS",
        "description_hashtags": "#Shorts #KPSS #KPSSGenelKultur #KPSS2026 #GenelKultur #SinavHazirlik",
        "tags": ["kpss", "kpss genel kultur", "kpss hazirlik", "genel kultur", "sinav sorulari"],
        "banner_title": "KPSS GÜNLÜĞÜM",
        "banner_tagline": "Her gün yeni bir KPSS Genel Kültür sorusu",
        "profile_pic_text": "KPSS",
        "channel_description": """Her gün yeni bir KPSS Genel Kültür sorusu!

Tarih, coğrafya, vatandaşlık, güncel bilgiler ve genel kültürden \
özgün deneme sorularıyla KPSS'ye hazırlan. Soruyu cevapla, \
cevabı öğren, bir sonrakini kaçırma.

Not: Bu kanaldaki sorular KPSS tarzında hazırlanmış özgün deneme \
sorularıdır; gerçek sınavda çıkmış sorular değildir.

Kaçırmamak için abone ol, her gün seninleyiz!

#KPSS #KPSSGenelKultur #SinavHazirlik
""",
    },
    "ehliyet": {
        "categories": [
            "trafik işaretleri ve levhalar", "ilkyardım uygulamaları", "motor ve araç bilgisi",
            "trafik kuralları ve ceza puanları", "ilk yardımda temel müdahaleler",
            "trafik adabı ve öncelik kuralları", "çevre bilgisi",
        ],
        "topic_label": "ehliyet (sürücü adaylığı) sınavı",
        "history_file": "history_ehliyet.json",
        "video_badge": "EHLİYET SORUSU",
        "guess_prompt": "Cevabı biliyor musun?",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni soru!",
        "title_hashtags": "#Shorts #Ehliyet",
        "description_hashtags": "#Shorts #Ehliyet #EhliyetSinavi #TrafikSorulari #SurucuAdayi #SinavHazirlik",
        "tags": ["ehliyet", "ehliyet sinavi", "trafik sorulari", "ilkyardim", "surucu adayi"],
        "banner_title": "EHLİYET SINAVIM",
        "banner_tagline": "Her gün yeni bir ehliyet sınavı sorusu",
        "profile_pic_text": "EHLİYET",
        "channel_description": """Her gün yeni bir ehliyet sınavı sorusu!

Trafik işaretleri, ilkyardım, motor bilgisi ve trafik kurallarından \
özgün deneme sorularıyla ehliyet sınavına hazırlan. Soruyu cevapla, \
cevabı öğren, bir sonrakini kaçırma.

Not: Bu kanaldaki sorular sınav tarzında hazırlanmış özgün deneme \
sorularıdır; gerçek sınavda çıkmış sorular değildir.

Kaçırmamak için abone ol, her gün seninleyiz!

#Ehliyet #EhliyetSinavi #TrafikSorulari #SinavHazirlik
""",
    },
    "tarihte_bugun": {
        "is_exam_prep": False,
        "date_aware": True,
        "categories": [
            "Türkiye tarihi", "dünya tarihi", "bilim ve keşifler tarihi",
            "sanat ve kültür tarihi", "spor tarihi",
        ],
        "topic_label": "Tarihte Bugün bilgi",
        "history_file": "history_tarihte_bugun.json",
        "video_badge": "TARİHTE BUGÜN",
        "guess_prompt": "Ne olduğunu biliyor musun?",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir tarih!",
        "title_hashtags": "#Shorts #TarihteBugün",
        "description_hashtags": "#Shorts #TarihteBugün #Tarih #GenelKultur #BilgiVideosu",
        "tags": ["tarihte bugun", "tarih", "genel kultur", "bilgi", "tarihi olaylar"],
        "banner_title": "TARİHTE BUGÜN",
        "banner_tagline": "Her gün o günün tarihi bir olayı",
        "profile_pic_text": "TARİH",
        "channel_description": """Her gün, o güne (ay ve gün) ait gerçek bir tarihi olay!

Türkiye tarihi, dünya tarihi, bilim, sanat ve spordan gerçek tarihi \
olaylarla her gün bir bilgi kartı. Soruyu cevapla, olayı öğren, \
bir sonrakini kaçırma.

Kaçırmamak için abone ol, her gün seninleyiz!

#TarihteBugün #Tarih #GenelKultur
""",
    },
    "ulke_baskent": {
        "is_exam_prep": False,
        "categories": [
            "Avrupa ülkeleri", "Asya ülkeleri", "Afrika ülkeleri",
            "Amerika kıtası ülkeleri", "Okyanusya ülkeleri", "Orta Doğu ülkeleri",
        ],
        "topic_label": "dünya ülkeleri ve başkentleri",
        "history_file": "history_ulke_baskent.json",
        "video_badge": "ÜLKE & BAŞKENT",
        "guess_prompt": "Biliyor musun?",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün bir ülke!",
        "title_hashtags": "#Shorts #Coğrafya",
        "description_hashtags": "#Shorts #Coğrafya #ÜlkelerVeBaşkentler #GenelKultur #Bilgi",
        "tags": ["ulkeler", "baskentler", "cografya", "genel kultur", "bilgi yarismasi"],
        "banner_title": "ÜLKELER & BAŞKENTLER",
        "banner_tagline": "Her gün bir ülke, bir başkent",
        "profile_pic_text": "DÜNYA",
        "channel_description": """Her gün bir ülke, bir başkent!

Dünyanın dört bir yanından ülke ve başkent bilgileriyle coğrafya \
bilgini test et. Soruyu cevapla, cevabı öğren, bir sonrakini kaçırma.

Kaçırmamak için abone ol, her gün seninleyiz!

#Coğrafya #ÜlkelerVeBaşkentler #GenelKultur
""",
    },
    "ingilizce_kelime": {
        "is_exam_prep": False,
        "categories": [
            "günlük hayat kelimeleri", "iş ve kariyer kelimeleri", "seyahat kelimeleri",
            "duygu ve karakter kelimeleri", "sık kullanılan fiiller", "sık kullanılan deyimler",
        ],
        "topic_label": "günlük İngilizce kelime öğrenme",
        "history_file": "history_ingilizce_kelime.json",
        "video_badge": "GÜNÜN KELİMESİ",
        "guess_prompt": "Anlamını biliyor musun?",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni kelime!",
        "title_hashtags": "#Shorts #İngilizce",
        "description_hashtags": "#Shorts #İngilizce #GünlükİngilizceKelime #EnglishWord #KelimeÖğren",
        "tags": ["ingilizce kelime", "ingilizce ogren", "gunluk ingilizce", "kelime hazinesi", "english vocabulary"],
        "banner_title": "GÜNÜN KELİMESİ",
        "banner_tagline": "Her gün yeni bir İngilizce kelime",
        "profile_pic_text": "WORD",
        "channel_description": """Her gün yeni bir İngilizce kelime!

Günlük hayat, iş ve seyahatte işine yarayacak İngilizce kelimeleri \
Türkçe anlamı ve örnek cümlesiyle öğren. Kelimeyi tahmin et, \
anlamını öğren, bir sonrakini kaçırma.

Kaçırmamak için abone ol, her gün seninleyiz!

#İngilizce #KelimeÖğren #EnglishVocabulary
""",
    },
}


def get_profile(name: str | None = None) -> dict:
    name = name or os.environ.get("CONTENT_PROFILE", "kpss")
    if name not in PROFILES:
        raise ValueError(f"Unknown CONTENT_PROFILE {name!r}. Choose from: {list(PROFILES)}")
    return {"name": name, **PROFILES[name]}
```

### `src/text_sanitize.py`

LLM'in ürettiği metni her zaman güvenli/temiz hale getirir. İki katman: (1)
yazım normalizasyonu (akıllı tırnaklar, markdown işaretleri temizlenir), (2)
kullanılan fontun gerçekten desteklediği karakterlere göre filtreleme (emoji
gibi fontta karşılığı olmayan karakterler otomatik düşürülür, tofu kutusu
hatası hiç oluşmaz).

```python
"""Cleans LLM-generated text so it always renders correctly on video and TTS.

Two layers:
  1. `normalize_text` — font-agnostic cleanup: smart quotes/dashes -> plain
     ASCII, markdown symbols stripped, whitespace collapsed. Applied right
     after parsing the Gemini response so narration and captions match.
  2. `filter_to_font` — drops/decomposes any character the target font can't
     actually render (emoji, exotic symbols), so text never shows as tofu
     boxes regardless of what the model outputs.
"""
import re
import unicodedata

_PUNCT_MAP = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2026": "...", "\u00a0": " ",
    "\u2022": "-", "\u2039": "<", "\u203a": ">",
}

_MARKDOWN_CHARS = re.compile(r"[*_`#~^]")
_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Font-agnostic cleanup: typographic punctuation -> plain ASCII, strip markdown."""
    if not text:
        return text
    for src, dst in _PUNCT_MAP.items():
        text = text.replace(src, dst)
    text = _MARKDOWN_CHARS.sub("", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text


_charset_cache = {}


def font_charset(font_path: str) -> set:
    """Returns the set of characters a .ttf file can actually render."""
    if font_path in _charset_cache:
        return _charset_cache[font_path]
    from fontTools.ttLib import TTFont

    ttfont = TTFont(font_path, lazy=True)
    cmap = ttfont.getBestCmap() or {}
    charset = {chr(code) for code in cmap.keys()}
    _charset_cache[font_path] = charset
    return charset


def filter_to_font(text: str, font_path: str | None) -> str:
    """Drops/decomposes characters the given font cannot render (e.g. emoji)."""
    if not text or not font_path:
        return text
    try:
        allowed = font_charset(font_path)
    except Exception:
        return text

    out = []
    for ch in text:
        if ch.isspace() or ch in allowed:
            out.append(ch)
            continue
        decomposed = unicodedata.normalize("NFKD", ch)
        decomposed = "".join(c for c in decomposed if not unicodedata.combining(c))
        if decomposed and all(c.isspace() or c in allowed for c in decomposed):
            out.append(decomposed)
        # otherwise silently drop the unsupported character (e.g. emoji)
    cleaned = "".join(out)
    return _WHITESPACE.sub(" ", cleaned).strip()
```

> **Not**: Yukarıdaki `_PUNCT_MAP` dict'inde karakterler unicode escape
> (`\u2018` gibi) olarak yazıldı çünkü bu dokümanın kendisi farklı
> encoding'lerde açılabiliyor. Gerçek dosyada bunlar doğrudan karakter olarak
> da yazılabilir (`'`, `'`, `"`, `"`, `–`, `—` vb.) — işlevsel olarak aynıdır.

### `src/generate_question.py`

```python
"""Generates an original Turkish trivia/exam-prep question using the free Google Gemini API tier.

Which channel (KPSS, ehliyet, tarihte_bugun, ...) is controlled by the
CONTENT_PROFILE env var / profiles.py.
"""
import datetime
import json
import os
import random

from google import genai
from google.genai import types

from profiles import get_profile
from text_sanitize import normalize_text

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
TURKISH_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]
# "-latest" alias so this keeps working as Google retires dated snapshots.
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


def load_history(history_path):
    if not os.path.exists(history_path):
        return {"questions": []}
    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history, history_path):
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def generate_question(profile: dict | None = None) -> dict:
    profile = profile or get_profile()
    history_path = os.path.join(DATA_DIR, profile["history_file"])

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    history = load_history(history_path)
    recent = [q["question"] for q in history["questions"][-50:]]
    category = random.choice(profile["categories"])

    avoid_block = ""
    if recent:
        avoid_list = "\n".join(f"- {q}" for q in recent)
        avoid_block = (
            "\nAşağıdaki daha önce kullanılmış sorularla aynı veya çok benzer bir soru üretme:\n"
            f"{avoid_list}\n"
        )

    if profile.get("is_exam_prep", True):
        intro = f"Sen, günlük YouTube Shorts {profile['topic_label']} hazırlık kanalı için soru yazan bir eğitmensin."
        task = f""""{category}" konusunda, {profile['topic_label']} tarzında, özgün BİR adet deneme sorusu üret.
Bu gerçek bir sınavda çıkmış soru DEĞİL, sınav formatına ve zorluk seviyesine uygun,
senin ürettiğin doğru ve güncel bilgilere dayanan orijinal bir deneme sorusu olmalı."""
    else:
        intro = f"Sen, günlük YouTube Shorts {profile['topic_label']} kanalı için içerik yazan bir eğitmensin."
        task = f""""{category}" konusunda, ilgi çekici ve bilgilendirici BİR adet trivia sorusu üret."""

    extra_instruction = ""
    if profile.get("date_aware"):
        today_date = datetime.date.today()
        today = f"{today_date.day} {TURKISH_MONTHS[today_date.month - 1]}"
        extra_instruction = (
            f"\nBugünün tarihi: {today}. Sorunun ve cevabın, tarihte bugün "
            "(ayın ve günün aynısı, yıl fark etmez) gerçekten yaşanmış doğru bir olaya "
            "dayanması ZORUNLU. Uydurma veya tarihi yanlış bir olay verme.\n"
        )

    prompt = f"""{intro}

{task}
Bilgiler kesin doğru ve güncel olmalı (özellikle ilkyardım, trafik kuralları gibi
güvenlik açısından kritik konularda ya da tarihi olaylarda yanlış bilgi verme).
Soru ilgi çekici, bilgilendirici ve birkaç kelimeyle cevaplanabilir olmalı.
{extra_instruction}{avoid_block}
Sadece düz noktalama işaretleri kullan (düz tırnak, tire), markdown, emoji veya özel sembol kullanma.
Tüm alanları Türkçe yaz (İngilizce kelime örnekleri gibi zorunlu durumlar hariç).
Türkçe karakterleri (ı, İ, ğ, ü, ş, ö, ç) doğru ve eksiksiz kullan; bunları
ASCII karşılıklarıyla (i, g, u, s, o, c) değiştirme."""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "question": {"type": "STRING"},
                    "answer": {"type": "STRING"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["question", "answer", "explanation"],
            },
        ),
    )
    data = json.loads(response.text)
    # We already picked `category` ourselves (in Turkish); don't let the model
    # regenerate it, since it sometimes drifts into an English paraphrase.
    data["category"] = category

    required = {"category", "question", "answer", "explanation"}
    if not required.issubset(data):
        raise ValueError(f"Model response missing fields: {data!r}")

    for field in required:
        data[field] = normalize_text(str(data[field]))

    history["questions"].append(
        {
            "category": data["category"],
            "question": data["question"],
            "answer": data["answer"],
        }
    )
    save_history(history, history_path)

    return data


if __name__ == "__main__":
    import sys

    p = get_profile(sys.argv[1] if len(sys.argv) > 1 else None)
    q = generate_question(p)
    print(json.dumps(q, indent=2, ensure_ascii=False))
```

### `src/tts.py`

```python
"""Free text-to-speech narration using edge-tts (no API key required)."""
import asyncio

import edge_tts

VOICE = "tr-TR-EmelNeural"


async def _synthesize(text: str, out_path: str, rate: str = "+0%"):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate)
    await communicate.save(out_path)


def synthesize(text: str, out_path: str, rate: str = "+0%"):
    """Render `text` to an mp3 file at `out_path`."""
    asyncio.run(_synthesize(text, out_path, rate))
    return out_path


if __name__ == "__main__":
    synthesize("Güneş sistemimizde en çok uyduya sahip gezegen hangisidir?", "test_tts.mp3")
    print("Wrote test_tts.mp3")
```

> Farklı bir dil/aksan istenirse `VOICE` değiştirilebilir. Mevcut seslerin
> listesi: `edge-tts --list-voices` komutuyla görülebilir (örn. erkek ses
> için `tr-TR-AhmetNeural`).

### `src/render_video.py`

Bu dosya en karmaşık olanı. PIL ile kare kare çizip MoviePy ile video haline
getiriyor. Uzun soru/cevaplarda metnin ekrandan taşmaması için font
boyutunu ve satır sarmasını otomatik küçülten (`_fit_text`), ve alt
elemanları (tahmin yazısı, geri sayım, açıklama) bir önceki bloğun gerçek
yüksekliğine göre dinamik konumlandıran (`_block_metrics`) bir mekanizma var
— bu, geliştirme sırasında karşılaşılan gerçek bir taşma bug'ının düzeltmesidir.

```python
"""Renders a 1080x1920 Shorts video for a trivia question using PIL + MoviePy.

No stock footage is used (avoids licensing issues and external downloads that
could fail in CI): the background is a procedurally generated animated gradient.
"""
import math
import os
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_audioclips

from profiles import get_profile
from text_sanitize import filter_to_font

W, H = 1080, 1920
FPS = 30

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT_DIR = os.path.join(ASSETS_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")

_FONT_CANDIDATES = [
    os.path.join(FONT_DIR, "Anton-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _find_font_path():
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def _font(size: int) -> ImageFont.FreeTypeFont:
    path = _find_font_path()
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


# --- background -------------------------------------------------------

_BG_TOP = np.array([20, 16, 60])
_BG_BOTTOM = np.array([90, 20, 120])


def _gradient_frame(t: float) -> np.ndarray:
    """Vertical gradient with a slow animated hue-shifting glow."""
    shift = (math.sin(t * 0.5) + 1) / 2  # 0..1
    top = _BG_TOP * (1 - shift * 0.3) + np.array([60, 10, 90]) * (shift * 0.3)
    bottom = _BG_BOTTOM * (1 - shift * 0.3) + np.array([10, 40, 110]) * (shift * 0.3)

    ramp = np.linspace(0, 1, H).reshape(H, 1, 1)
    grad = top.reshape(1, 1, 3) * (1 - ramp) + bottom.reshape(1, 1, 3) * ramp
    frame = np.repeat(grad, W, axis=1).astype(np.uint8)

    # soft moving glow blob for a bit of life
    yy, xx = np.mgrid[0:H, 0:W]
    cx = W / 2 + math.sin(t * 0.4) * 250
    cy = H * 0.35 + math.cos(t * 0.3) * 200
    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    glow = np.exp(-dist2 / (2 * (420 ** 2))) * 40
    frame = np.clip(frame + glow[..., None], 0, 255).astype(np.uint8)
    return frame


# --- text helpers -------------------------------------------------------


def _wrap(text: str, width: int) -> list:
    return textwrap.wrap(text, width=width)


def _block_metrics(draw, lines, font, stroke_width, line_spacing=1.15):
    """Returns (line_height, total_height) for a wrapped block, without drawing it."""
    if not lines:
        return 0, 0
    sizes = [draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width) for line in lines]
    heights = [b[3] - b[1] for b in sizes]
    line_h = max(heights) * line_spacing
    return line_h, line_h * len(lines)


def _draw_text_block(draw, lines, font, center_x, center_y, fill, stroke_fill, stroke_width, line_spacing=1.15):
    line_h, total_h = _block_metrics(draw, lines, font, stroke_width, line_spacing)
    sizes = [draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width) for line in lines]
    y = center_y - total_h / 2
    for line, bbox in zip(lines, sizes):
        w = bbox[2] - bbox[0]
        x = center_x - w / 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += line_h


def _fit_text(text, max_font, min_font, base_wrap, max_lines, step_font=6, step_wrap=3):
    """Shrinks font size / widens wrapping until the text fits within max_lines,
    so long questions/answers never overflow into neighboring elements."""
    font_size = max_font
    wrap_width = base_wrap
    while True:
        lines = _wrap(text, wrap_width)
        if len(lines) <= max_lines or font_size <= min_font:
            return _font(font_size), lines
        font_size -= step_font
        wrap_width += step_wrap


def _badge(draw, text, cy, font, fg="#0B0B14", bg="#FFD400"):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 36, 18
    box_w, box_h = tw + pad_x * 2, th + pad_y * 2
    x0 = (W - box_w) / 2
    y0 = cy - box_h / 2
    draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=box_h / 2, fill=bg)
    draw.text((W / 2 - tw / 2, y0 + pad_y - bbox[1]), text, font=font, fill=fg)


def _ease_out(p):
    return 1 - (1 - p) ** 3


# --- scene timings -------------------------------------------------------
INTRO_DUR = 1.6
QUESTION_IN_DUR = 0.5
COUNTDOWN_DUR = 4.0
REVEAL_IN_DUR = 0.5
OUTRO_DUR = 2.0


def build_video(question: dict, question_audio: str, answer_audio: str, out_path: str, profile: dict | None = None):
    profile = profile or get_profile()
    font_path = _find_font_path()
    question = {
        **question,
        "category": filter_to_font(question["category"], font_path),
        "question": filter_to_font(question["question"], font_path),
        "answer": filter_to_font(question["answer"], font_path),
        "explanation": filter_to_font(question["explanation"], font_path),
    }

    q_clip = AudioFileClip(question_audio)
    a_clip = AudioFileClip(answer_audio)

    question_start = INTRO_DUR + QUESTION_IN_DUR
    question_narration_end = question_start + q_clip.duration
    countdown_start = question_narration_end
    countdown_end = countdown_start + COUNTDOWN_DUR
    reveal_start = countdown_end + REVEAL_IN_DUR
    reveal_narration_end = reveal_start + a_clip.duration
    outro_start = reveal_narration_end
    total_duration = outro_start + OUTRO_DUR

    font_badge = _font(46)
    font_answer_label = _font(50)
    font_explain = _font(42)
    font_outro = _font(56)
    font_countdown = _font(140)

    _measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    font_q, q_lines = _fit_text(question["question"], max_font=64, min_font=38, base_wrap=22, max_lines=6)
    _, q_block_h = _block_metrics(_measure_draw, q_lines, font_q, stroke_width=8)

    font_answer, a_lines = _fit_text(question["answer"], max_font=72, min_font=40, base_wrap=16, max_lines=4)
    _, a_block_h = _block_metrics(_measure_draw, a_lines, font_answer, stroke_width=8)

    def make_frame(t):
        bg = _gradient_frame(t)
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        if t < INTRO_DUR:
            p = _ease_out(min(t / 0.6, 1.0))
            alpha_badge_y = H * 0.42 + (1 - p) * 40
            _badge(draw, profile["video_badge"], alpha_badge_y, font_badge)
            if t > 0.6:
                p2 = _ease_out(min((t - 0.6) / 0.6, 1.0))
                cat_text = question["category"].upper()
                draw.text(
                    (W / 2, H * 0.55 + (1 - p2) * 30), cat_text,
                    font=font_answer_label, fill=(255, 255, 255, int(255 * p2)),
                    anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0),
                )

        elif t < countdown_start:
            _badge(draw, question["category"].upper(), H * 0.14, font_badge)
            p = _ease_out(min((t - INTRO_DUR) / QUESTION_IN_DUR, 1.0))
            block_top = H * 0.26 + (1 - p) * 30
            _draw_text_block(
                draw, q_lines, font_q, W / 2, block_top + q_block_h / 2,
                fill="#FFFFFF", stroke_fill="#000000", stroke_width=8,
            )
            guess_y = min(max(H * 0.62, block_top + q_block_h + 70), H * 0.85)
            draw.text((W / 2, guess_y), profile["guess_prompt"], font=font_answer_label,
                       fill="#FFD400", anchor="mm", stroke_width=3, stroke_fill="#000000")

        elif t < reveal_start:
            _badge(draw, question["category"].upper(), H * 0.14, font_badge)
            block_top = H * 0.20
            _draw_text_block(
                draw, q_lines, font_q, W / 2, block_top + q_block_h / 2,
                fill="#FFFFFF", stroke_fill="#000000", stroke_width=8,
            )
            remaining = max(0, countdown_end - t)
            count_val = int(math.ceil(remaining))
            count_val = max(1, min(count_val, int(COUNTDOWN_DUR)))
            frac = remaining - math.floor(remaining)
            scale = 1.0 + 0.15 * frac
            r = 130 * scale
            cx = W / 2
            cy = min(max(H * 0.68, block_top + q_block_h + 180), H * 0.85)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#FFD400", width=10)
            draw.text((cx, cy), str(count_val), font=font_countdown, fill="#FFD400",
                       anchor="mm", stroke_width=4, stroke_fill="#000000")

        elif t < outro_start:
            p = _ease_out(min((t - countdown_end) / REVEAL_IN_DUR, 1.0))
            draw.rectangle([0, 0, W, H], fill=(10, 90, 40))
            bg2 = _gradient_frame(t)
            blended = (np.array(bg2, dtype=float) * 0.25 + np.array([15, 90, 45]) * 0.75).astype(np.uint8)
            img = Image.fromarray(blended)
            draw = ImageDraw.Draw(img)

            draw.text((W / 2, H * 0.16 + (1 - p) * 20), "CEVAP", font=font_answer_label,
                       fill="#FFFFFF", anchor="mm", stroke_width=3, stroke_fill="#000000")
            answer_top = H * 0.24 + (1 - p) * 20
            _draw_text_block(
                draw, a_lines, font_answer, W / 2, answer_top + a_block_h / 2,
                fill="#FFD400", stroke_fill="#000000", stroke_width=8,
            )
            if t > reveal_start + 0.3:
                exp_lines = _wrap(question["explanation"], 30)
                exp_y = min(max(H * 0.52, answer_top + a_block_h + 70), H * 0.75)
                _draw_text_block(
                    draw, exp_lines, font_explain, W / 2, exp_y,
                    fill="#FFFFFF", stroke_fill="#000000", stroke_width=5, line_spacing=1.3,
                )

        else:
            draw.text((W / 2, H * 0.44), profile["outro_line1"], font=font_outro, fill="#FFFFFF",
                       anchor="mm", stroke_width=5, stroke_fill="#000000")
            draw.text((W / 2, H * 0.51), profile["outro_line2"], font=font_outro, fill="#FFD400",
                       anchor="mm", stroke_width=5, stroke_fill="#000000")

        return np.array(img)

    # Grab a frame from the question scene (not the answer reveal!) to use as
    # the YouTube thumbnail, so the auto-selected preview doesn't spoil the answer.
    thumb_time = max(question_start + 0.1, min(question_start + 0.6, countdown_start - 0.2))
    thumb_path = os.path.splitext(out_path)[0] + "_thumb.jpg"
    Image.fromarray(make_frame(thumb_time)).convert("RGB").save(thumb_path, quality=90)

    video = VideoClip(make_frame, duration=total_duration).with_fps(FPS)

    q_audio_positioned = q_clip.with_start(question_start)
    a_audio_positioned = a_clip.with_start(reveal_start)
    audio = CompositeAudioClip([q_audio_positioned, a_audio_positioned])

    music_path = _find_music()
    if music_path:
        music = AudioFileClip(music_path).with_volume_scaled(0.12)
        if music.duration < total_duration:
            loops = int(total_duration / music.duration) + 1
            music = concatenate_audioclips([music] * loops)
        music = music.subclipped(0, total_duration)
        audio = CompositeAudioClip([music, q_audio_positioned, a_audio_positioned])

    video = video.with_audio(audio)
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )
    return out_path


def _find_music():
    if not os.path.isdir(MUSIC_DIR):
        return None
    for name in os.listdir(MUSIC_DIR):
        if name.lower().endswith((".mp3", ".m4a", ".wav")):
            return os.path.join(MUSIC_DIR, name)
    return None


if __name__ == "__main__":
    from tts import synthesize

    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    demo_question = {
        "category": "Türkiye coğrafyası",
        "question": "Türkiye'nin en yüksek dağı hangisidir?",
        "answer": "Ağrı Dağı",
        "explanation": "Ağrı Dağı, 5137 metre yüksekliğiyle Türkiye'nin en yüksek noktasıdır.",
    }
    q_path = os.path.join(out_dir, "_q.mp3")
    a_path = os.path.join(out_dir, "_a.mp3")
    video_path = os.path.join(out_dir, "demo.mp4")
    synthesize(demo_question["question"], q_path)
    synthesize(f"Cevap: {demo_question['answer']}. {demo_question['explanation']}", a_path)
    build_video(demo_question, q_path, a_path, video_path)
    print(f"Wrote {video_path}")
```

### `src/upload_youtube.py`

```python
"""Uploads a rendered Short to YouTube via the YouTube Data API v3.

Auth uses a pre-obtained OAuth refresh token (see setup/get_refresh_token.py)
supplied through environment variables so this can run unattended in CI.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from profiles import get_profile

SCOPES = ["https://www.googleapis.com/auth/youtube"]


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

    description = (
        f"{question['question']}\n\n"
        f"Cevap: {question['answer']}\n"
        f"{question['explanation']}\n\n"
        f"{profile['description_hashtags']}"
    )
    tags = [*profile["tags"], question["category"]]
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
```

### `src/main.py`

```python
"""Orchestrates the full daily pipeline: generate -> narrate -> render -> upload.

Which channel/exam this runs for is picked via the CONTENT_PROFILE env var
(see profiles.py), so the same code drives every exam-prep channel.
"""
import argparse
import os

from generate_question import generate_question
from profiles import get_profile
from render_video import build_video
from tts import synthesize
from upload_youtube import upload_video

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def run(upload: bool = True):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    profile = get_profile()
    print(f"Profile: {profile['name']}")

    print("Generating question...")
    question = generate_question(profile)
    print(f"  {question['category']}: {question['question']} -> {question['answer']}")

    q_audio = os.path.join(OUTPUT_DIR, "question.mp3")
    a_audio = os.path.join(OUTPUT_DIR, "answer.mp3")
    print("Synthesizing narration...")
    synthesize(question["question"], q_audio)
    synthesize(f"Cevap: {question['answer']}. {question['explanation']}", a_audio)

    video_path = os.path.join(OUTPUT_DIR, "short.mp4")
    thumb_path = os.path.join(OUTPUT_DIR, "short_thumb.jpg")
    print("Rendering video...")
    build_video(question, q_audio, a_audio, video_path, profile)
    print(f"  wrote {video_path}")

    if upload:
        print("Uploading to YouTube...")
        upload_video(video_path, question, thumbnail_path=thumb_path, profile=profile)
    else:
        print("Skipping upload (--no-upload).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-upload", action="store_true", help="Render locally without uploading to YouTube")
    args = parser.parse_args()
    run(upload=not args.no_upload)
```

### `setup/get_refresh_token.py`

Bu script SADECE lokalde, insan tarafından, tarayıcı ile bir kere çalıştırılır
(her yeni kanal için bir kez). CI'da (GitHub Actions'ta) ÇALIŞTIRILMAZ.

```python
"""One-time local script to obtain a YouTube OAuth refresh token.

Run this once on your own machine (NOT in CI):

    python setup/get_refresh_token.py

It opens a browser for you to sign in with the Google account that owns
your YouTube channel, then prints the refresh token to copy into your
GitHub repo secrets as YT_REFRESH_TOKEN (along with YT_CLIENT_ID and
YT_CLIENT_SECRET taken from client_secret.json).

Requires a `client_secret.json` (OAuth "Desktop app" client) downloaded
from Google Cloud Console, placed next to this script or in the project root.
"""
import json
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube"]

CANDIDATE_PATHS = [
    "client_secret.json",
    os.path.join(os.path.dirname(__file__), "client_secret.json"),
    os.path.join(os.path.dirname(__file__), "..", "client_secret.json"),
]


def find_client_secret():
    for path in CANDIDATE_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "client_secret.json not found. Download it from Google Cloud Console "
        "(APIs & Services > Credentials > OAuth client ID > Desktop app) and "
        "place it in the project root or setup/ folder."
    )


def main():
    client_secret_path = find_client_secret()
    with open(client_secret_path) as f:
        client_config = json.load(f)

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # Force Google to show account/channel selection again instead of silently
    # reusing a previously-granted (possibly wrong) channel.
    creds = flow.run_local_server(port=0, prompt="consent select_account")

    key = "installed" if "installed" in client_config else "web"
    client_id = client_config[key]["client_id"]
    client_secret = client_config[key]["client_secret"]

    print("\nSuccess! Add these as GitHub repo secrets:\n")
    print(f"YT_CLIENT_ID={client_id}")
    print(f"YT_CLIENT_SECRET={client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
```

**ÇOK ÖNEMLİ — kanal seçimi gotcha'sı**: Eğer Google hesabında birden fazla
YouTube kanalı varsa (kişisel kanal + marka hesapları), bu script'i
çalıştırdığında Google'ın "hangi kanal olarak devam etmek istiyorsun" diye
ayrı bir seçim ekranı GÖSTERMEME ihtimali yüksek — genelde otomatik olarak
hesabın "varsayılan/birincil" kanalını seçer. Doğru kanala bağlanmak için:

1. Script'i çalıştırmadan HEMEN ÖNCE, tarayıcıda youtube.com'a git ve o an
   hedeflediğin kanalı (marka hesabını) **aktif kanal** yap (genelde bu,
   kanalı yeni oluşturduysan zaten otomatik aktif olur).
2. Script'i çalıştır, Google hesabıyla giriş yap, izin ver.
3. **MUTLAKA DOĞRULA**: `channels().list(part='snippet', mine=True)` çağrısı
   yapıp dönen kanal adının beklediğin kanal olduğunu kontrol et (aşağıda
   "Doğrulama" bölümünde tam kod var).
4. Yanlış kanala bağlandıysa: [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
   adresinden uygulamanın erişimini tamamen kaldır (Remove Access), sonra
   1-3 adımlarını tekrarla. Genelde temiz bir yetki iptali + doğru kanalın
   aktif olması kombinasyonu sorunu çözer.

### `setup/channel_branding.py`

Bir kanalın banner'ını, açıklamasını ve profil resmini (marka renklerine
uygun, kod ile üretilmiş) otomatik oluşturup YouTube'a gönderir.

```python
"""One-time script to generate channel branding assets (banner + profile picture)
and push the banner + description to a YouTube channel via the API.

The YouTube Data API has no endpoint to set the channel profile picture/avatar,
so that PNG is generated locally and must be uploaded manually in YouTube Studio
(Channel customization -> Branding -> Picture -> Upload).

Usage (from the project root), credentials for the TARGET channel:
    YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... \
        python setup/channel_branding.py <profile-name>

<profile-name> is one of the keys in src/profiles.py (e.g. kpss, ehliyet).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from profiles import get_profile  # noqa: E402
from upload_youtube import _get_credentials  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402
from googleapiclient.http import MediaFileUpload  # noqa: E402

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "Anton-Regular.ttf")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "branding")


def _font(size):
    return ImageFont.truetype(FONT_PATH, size)


def _gradient(w, h):
    top = np.array([20, 16, 60])
    bottom = np.array([70, 18, 100])
    ramp = np.linspace(0, 1, h).reshape(h, 1, 1)
    grad = top.reshape(1, 1, 3) * (1 - ramp) + bottom.reshape(1, 1, 3) * ramp
    frame = np.repeat(grad, w, axis=1).astype(np.uint8)

    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h * 0.4
    dist2 = (xx - cx) ** 2 + (yy - cy) ** 2
    glow = np.exp(-dist2 / (2 * (min(w, h) * 0.35) ** 2)) * 45
    frame = np.clip(frame + glow[..., None], 0, 255).astype(np.uint8)
    return Image.fromarray(frame)


def make_banner(path, title_line, tagline):
    w, h = 2560, 1440
    img = _gradient(w, h)
    draw = ImageDraw.Draw(img)

    font_title = _font(150)
    font_tag = _font(56)

    cy = h / 2
    draw.text((w / 2, cy - 60), title_line, font=font_title, fill="#FFD400",
              anchor="mm", stroke_width=10, stroke_fill="#000000")
    draw.text((w / 2, cy + 90), tagline, font=font_tag, fill="#FFFFFF",
              anchor="mm", stroke_width=4, stroke_fill="#000000")

    img.save(path)
    return path


def make_profile_picture(path, badge_text):
    size = 800
    img = _gradient(size, size)
    draw = ImageDraw.Draw(img)
    font_size = 190 if len(badge_text) <= 4 else 120
    font = _font(font_size)
    draw.text((size / 2, size / 2 - 10), badge_text, font=font, fill="#FFD400",
              anchor="mm", stroke_width=10, stroke_fill="#000000")
    img.save(path)
    return path


def push_to_youtube(banner_path, description):
    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    channel_id = youtube.channels().list(part="id", mine=True).execute()["items"][0]["id"]

    banner_media = MediaFileUpload(banner_path, mimetype="image/png")
    banner_resp = youtube.channelBanners().insert(media_body=banner_media).execute()
    banner_url = banner_resp["url"]

    youtube.channels().update(
        part="brandingSettings",
        body={
            "id": channel_id,
            "brandingSettings": {
                "channel": {"description": description},
                "image": {"bannerExternalUrl": banner_url},
            },
        },
    ).execute()
    print("Banner and description updated on channel", channel_id)


if __name__ == "__main__":
    profile = get_profile(sys.argv[1] if len(sys.argv) > 1 else None)
    out_dir = os.path.join(OUT_DIR, profile["name"])
    os.makedirs(out_dir, exist_ok=True)

    banner_path = make_banner(
        os.path.join(out_dir, "banner.png"), profile["banner_title"], profile["banner_tagline"]
    )
    profile_pic_path = make_profile_picture(
        os.path.join(out_dir, "profile.png"), profile["profile_pic_text"]
    )
    print("Wrote", banner_path)
    print("Wrote", profile_pic_path)

    push_to_youtube(banner_path, profile["channel_description"])
    print("\nProfil resmi API ile ayarlanamiyor - YouTube Studio > Kanal ozellestirme > Resim > Yukle'den")
    print(f"su dosyayi manuel yukle: {profile_pic_path}")
```

### `.github/workflows/daily_short_<profil-adi>.yml`

Her kanal için bu şablonun bir kopyası oluşturulur; sadece `name`, `cron`,
`CONTENT_PROFILE`, secret adları ve `git add`/commit mesajındaki dosya adı
değişir. Örnek (KPSS):

```yaml
name: Daily KPSS Short

on:
  schedule:
    - cron: "0 17 * * *"   # 20:00 Turkey time (UTC+3)
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  publish:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v7

      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Generate, render and upload today's short
        working-directory: src
        env:
          CONTENT_PROFILE: kpss
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          YT_CLIENT_ID: ${{ secrets.YT_CLIENT_ID }}
          YT_CLIENT_SECRET: ${{ secrets.YT_CLIENT_SECRET }}
          YT_REFRESH_TOKEN: ${{ secrets.YT_REFRESH_TOKEN }}
        run: python main.py

      - name: Commit updated question history
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add data/history_kpss.json
          git diff --cached --quiet && exit 0
          git commit -m "chore: log today's KPSS question"
          for i in 1 2 3 4 5; do
            git pull --rebase origin main && git push && exit 0
            sleep 5
          done
          exit 1
```

> **Neden `git pull --rebase` + retry döngüsü var?** Aynı repoda birden fazla
> kanal workflow'u varsa (her biri kendi zamanında tetiklense de, manuel
> `workflow_dispatch` ile aynı anda tetiklenebilirler), ikisi de aynı anda
> `git push` yapmaya çalışırsa biri "reddedildi" hatası alır. Bu döngü, push
> reddedilirse önce `origin/main`'i çekip rebase yapar, sonra tekrar dener
> (5 kez, 5'er saniye arayla) — böylece iş asla sessizce başarısız olmaz.

> **Node.js 20 deprecation uyarısı**: `actions/checkout` ve
> `actions/setup-python` action'larının GÜNCEL major versiyonlarını (v7)
> kullanın — v4/v5 gibi eski versiyonlar GitHub'ın Node.js 20 desteğini
> kaldırmasıyla ileride sorun çıkarabilir.

---

## 4. Kurulum Adımları (Sırayla)

### Adım 0 — Gereken araçlar (lokal makinede)

- Python 3.12+
- `ffmpeg` (MoviePy bunu kullanır; Windows'ta `winget install ffmpeg` ile
  kurulabilir)
- `git`
- GitHub hesabı
- Google hesabı (YouTube kanalları bu hesap altında oluşturulacak)

```bash
pip install -r requirements.txt
```

### Adım 1 — Google Cloud projesi + API'ler

1. [console.cloud.google.com](https://console.cloud.google.com) → yeni proje
   oluştur (veya mevcut birini kullan).
2. **APIs & Services → Library** → "YouTube Data API v3" ara → **Enable**.

### Adım 2 — OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External**.
3. Uygulama adı, destek e-postası vb. gerekli alanları doldur.
4. Yayın durumu (Publishing status) **"Testing"** olarak kalabilir (uygulamayı
   Google'a doğrulatmaya gerek yok — kişisel kullanım için).
5. **Audience / Test users** sekmesine git → **+ ADD USERS** → kendi Gmail
   adresini ekle → Save. (Bu adım atlanırsa OAuth'ta "Error 403: access_denied"
   hatası alınır.)

### Adım 3 — OAuth Client ID (Desktop app)

1. **APIs & Services → Credentials → + CREATE CREDENTIALS → OAuth client ID**.
2. Application type: **Desktop app**.
3. Bir isim ver, **Create**.
4. **DOWNLOAD JSON** → dosyayı `client_secret.json` adıyla proje kök dizinine
   koy (bu dosya `.gitignore`'da, ASLA commit'lenmemeli).

### Adım 4 — Gemini API anahtarı

1. [aistudio.google.com/apikey](https://aistudio.google.com/apikey) → ücretsiz
   API key oluştur (kredi kartı istemez).
2. Bu anahtarı not al — `GEMINI_API_KEY` olarak kullanılacak.

### Adım 5 — GitHub reposu

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<kullanici>/<repo-adi>.git
git branch -M main
git push -u origin main
```

(`gh` CLI kuruluysa `gh repo create <repo-adi> --public --source=. --push`
tek satırda hallediyor.)

### Adım 6 — Her kanal için: YouTube kanalı oluştur + OAuth + secrets

Bu adımlar **her yeni kanal için tekrarlanır**. İlk kanaldan başlayın.

1. **Kanalı oluştur**: [youtube.com/channel_switcher](https://www.youtube.com/channel_switcher)
   → "Kanal oluştur" → istenen ismi ver (örn. "Günün Kelimesi").
   > ⚠️ Kanal oluşturma işleminin resmi bir API'si YOK — bu adım MUTLAKA
   > tarayıcıdan, insan tarafından yapılmalı.

2. **OAuth token al** (bu kanal tarayıcıda aktifken):
   ```bash
   python setup/get_refresh_token.py
   ```
   Açılan tarayıcı ekranında doğru Google hesabıyla giriş yap, izin ver.
   Script şunu yazdıracak:
   ```
   YT_CLIENT_ID=...
   YT_CLIENT_SECRET=...
   YT_REFRESH_TOKEN=...
   ```

3. **Doğrula** — bu token'ın gerçekten doğru kanala bağlandığını kontrol et
   (bu adımı ASLA atlama, yanlış kanala bağlanma çok sık yaşanan bir hata):
   ```python
   import os
   os.environ["YT_CLIENT_ID"] = "..."
   os.environ["YT_CLIENT_SECRET"] = "..."
   os.environ["YT_REFRESH_TOKEN"] = "..."

   import sys; sys.path.insert(0, "src")
   from upload_youtube import _get_credentials
   from googleapiclient.discovery import build
   creds = _get_credentials()
   youtube = build("youtube", "v3", credentials=creds)
   resp = youtube.channels().list(part="snippet", mine=True).execute()
   print(resp["items"][0]["snippet"]["title"])  # beklenen kanal adı çıkmalı
   ```
   Yanlış kanal çıkarsa: [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
   → uygulamanın erişimini kaldır → Adım 6.2'yi tekrarla.

4. **GitHub secret'larını ekle** (`gh` CLI ile, ya da GitHub web arayüzünden
   Settings → Secrets and variables → Actions → New repository secret):
   ```bash
   gh secret set GEMINI_API_KEY --body "<gemini-anahtari>"       # sadece ilk kanalda, tüm kanallar paylaşır
   gh secret set <ONEK>_YT_CLIENT_ID --body "<client-id>"
   gh secret set <ONEK>_YT_CLIENT_SECRET --body "<client-secret>"
   gh secret set <ONEK>_YT_REFRESH_TOKEN --body "<refresh-token>"
   ```
   `<ONEK>` = kanalın profil adının BÜYÜK harfli, alt çizgisiz hali (örn.
   `ingilizce_kelime` → `INGILIZCEKELIME`). İlk kanal için düz `YT_CLIENT_ID`
   vb. (öneksiz) kullanılabilir, sonrakiler için önek şart (aksi halde
   secret'lar birbirini ezer).

5. **Branding gönder** (banner + açıklama otomatik, profil resmi manuel):
   ```bash
   YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... \
     python setup/channel_branding.py <profil-adi>
   ```
   Çıktıda verilen `profile.png` dosyasını YouTube Studio → Kanal
   özelleştirme → Resim → Yükle'den manuel olarak yükle (API bunu
   desteklemiyor).

6. **Workflow dosyasını oluştur**: yukarıdaki şablonu kopyalayıp
   `CONTENT_PROFILE`, secret önekleri, cron saati ve dosya adını değiştir.

7. **İlk videoyu test et** (lokalde, gerçek yükleme ile):
   ```bash
   cd src
   CONTENT_PROFILE=<profil-adi> \
   GEMINI_API_KEY=... YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... \
   python main.py
   ```
   Ya da GitHub'a push ettikten sonra Actions sekmesinden "Run workflow" ile.

### Adım 7 — Bir sonraki kanal için Adım 6'yı tekrarla

---

## 5. Yeni Bir Kanal/Profil Eklemek (Sistem Kurulduktan Sonra)

1. `src/profiles.py` içine yeni bir dict ekle (yukarıdaki 5 örnekten birini
   kopyalayıp içeriğini değiştir — `categories`, `topic_label`,
   `video_badge`, `guess_prompt`, `outro_line1/2`, `title_hashtags`,
   `description_hashtags`, `tags`, `banner_title`, `banner_tagline`,
   `profile_pic_text`, `channel_description`, `history_file`).
2. Sınav hazırlık değilse (`is_exam_prep: False`) — genel trivia/bilgi
   formatı kullanılır, prompt "sınav" dilinden kaçınır.
3. Tarihe bağlı içerikse (`date_aware: True`) — bugünün tarihine göre
   üretim yapılır (bkz. "Tarihte Bugün" profili).
4. Boş bir `data/history_<profil-adi>.json` oluştur: `{"questions": []}`.
5. `.github/workflows/daily_short_<profil-adi>.yml` oluştur (şablonu
   kopyala, farklı bir cron saati seç — bkz. aşağıdaki zamanlama stratejisi).
6. Yukarıdaki "Adım 6" sürecini (kanal oluştur → OAuth → secrets → branding)
   uygula.

**Kod tarafında BAŞKA HİÇBİR ŞEYE dokunulmaz** — `generate_question.py`,
`render_video.py`, `upload_youtube.py`, `tts.py`, `main.py` tamamen
profil-agnostiktir.

---

## 6. Bilinen Sınırlamalar ve Öğrenilen Dersler

Bunlar gerçek geliştirme sürecinde karşılaşılan, çözülmüş veya bilinçli
olarak kabul edilmiş sorunlardır. Aynı hatalara tekrar düşmemek için okunmalı.

1. **`google-generativeai` paketi tamamen kullanımdan kaldırıldı.** Yeni
   `google-genai` paketi kullanılmalı (`from google import genai`). Eski
   paket + eski model adları (`gemini-2.5-flash` gibi tarihli/donuk isimler)
   404 hatası verir. Bunun yerine `gemini-flash-latest` alias'ı kullanılır —
   Google modelleri emekliye ayırdıkça bu alias otomatik güncel modele işaret
   eder, kod bir daha bozulmaz.

2. **Kategori alanını modele ürettirmeyin.** Gemini'ye "category" alanını da
   JSON'da doldurmasını isterseniz, bazen verdiğiniz Türkçe kategoriyi
   İngilizce'ye çevirip özetleyebiliyor (örn. "Amerika kıtası ülkeleri" →
   "Americas"). Kategoriyi siz seçip (random.choice), yanıttan bağımsız
   olarak kendiniz set edin.

3. **Türkçe karakterler bazen ASCII'ye kayabiliyor** ("Dünyada" yerine
   "Dunyada" gibi). Prompt'a açık bir "Türkçe karakterleri (ı, ğ, ü, ş, ö, ç)
   ASCII karşılıklarıyla değiştirme" uyarısı eklemek bu riski büyük ölçüde
   azaltıyor (garanti değil, LLM stokastik).

4. **YouTube Shorts'ta özel kapak (thumbnail) belirlemek sadece mobil
   uygulamadan mümkün.** Ne YouTube Data API'nin `thumbnails.set` metodu, ne
   de masaüstü Studio arayüzü buna izin veriyor (kanal doğrulanmış olsa
   bile) — "The authenticated user doesn't have permissions to upload and
   set custom video thumbnails" hatası kalıcıdır. Bu yüzden video render
   sırasında sorunun gösterildiği (cevabın DEĞİL) bir kare otomatik seçilip
   kaydediliyor (`thumb_time` hesaplaması), yükleme sonrası `thumbnails.set`
   deneniyor ama başarısız olursa (beklenen davranış) pipeline durmuyor,
   sadece log'a yazıp devam ediyor. Gerçek çözüm isteniyorsa kullanıcı
   telefon uygulamasından manuel düzeltebilir.

5. **Uzun soru/cevap metinleri sabit pozisyonlu elemanların üzerine
   taşabilir.** İlk versiyonda soru metni sabit bir Y koordinatında ortalanıp
   "Cevabı biliyor musun?" yazısı da sabit bir Y'de çiziliyordu — uzun bir
   soru (6+ satır) bu sabit yazının üzerine biniyordu. Çözüm:
   `_fit_text()` (font küçültme + satır genişletme, max satır sayısına göre)
   + sonraki elemanların pozisyonunu ÖNCEKİ BLOĞUN GERÇEK YÜKSEKLİĞİNE göre
   dinamik hesaplamak (`_block_metrics`). Yeni bir kanal/kategori eklerken bu
   mekanizmaya dokunmaya gerek yok, otomatik çalışır.

6. **Tek bir Google hesabında birden fazla YouTube kanalı olduğunda OAuth
   kafası karışabilir.** `mine=True` parametresi, o an "aktif" olan kanalı
   hedefler; bu genelde hesabın kişisel/varsayılan kanalıdır, marka hesabı
   DEĞİL. Google bazen "hangi kanal olarak devam et" seçim ekranını
   göstermiyor. Güvenilir çözüm: yeni kanalı oluşturduktan HEMEN SONRA (o an
   tarayıcıda otomatik aktif oluyor) OAuth akışını çalıştırmak, ve HER
   SEFERİNDE `channels().list(mine=True)` ile doğrulamak. Yanlış kanala
   bağlandıysa myaccount.google.com/permissions'tan erişimi iptal edip
   temiz baştan denemek genelde işe yarıyor.

7. **Tek hesaptan çok hızlı çok sayıda kanal açmak risklidir.** YouTube'un
   spam/bot tespit sistemleri, kısa sürede birden fazla otomatik-video-
   yükleyen kanal açan bir hesabı işaretleyebilir — bu, YENİ kanalları değil,
   hesaptaki TÜM kanalları (zaten çalışanlar dahil) askıya alma riski taşır.
   Kademeli büyümek (birkaç kanal, sonra bekle-gözlemle, sonra devam et)
   daha güvenli.

8. **Windows'ta lokal test ederken konsol çıktısı bozuk görünebilir**
   (Türkçe karakterler `?` veya mojibake olarak basılabilir). Bu sadece
   terminal codepage sorunu, gerçek dosyalara yazılan veri her zaman doğru
   UTF-8'dir. `PYTHONIOENCODING=utf-8` ortam değişkeniyle konsol çıktısı da
   düzeltilebilir.

9. **`MediaFileUpload` ile resumable upload kullanılıyor** (`resumable=True`)
   — büyük video dosyalarının yükleme sırasında kesintiye uğraması
   durumunda GitHub Actions runner'ının kısıtlı bant genişliğinde daha
   güvenilir çalışır.

10. **Aynı repoda birden fazla workflow varsa, `history_*.json` commit'leri
    çakışabilir** (iki workflow aynı anda push etmeye çalışırsa biri
    reddedilir). Çözüm: her workflow'un commit adımı `git pull --rebase`
    + 5 denemeli retry döngüsü içeriyor (yukarıdaki YAML şablonunda mevcut).

---

## 7. Test / Doğrulama Kontrol Listesi

Her yeni kanal kurulduktan sonra bunları sırayla kontrol edin:

- [ ] `python src/generate_question.py <profil-adi>` → geçerli JSON, doğru
      dilde/karakterde, doğru kategoriden bir soru üretiyor mu?
- [ ] `cd src && python main.py --no-upload` (CONTENT_PROFILE ile) →
      `output/short.mp4` hatasız render oluyor mu?
- [ ] Render edilen videodan birkaç kare çıkarıp (`ffmpeg -ss X -i short.mp4
      -frames:v 1 frame.png`) görsel olarak kontrol edin: metin taşması var
      mı, Türkçe karakterler doğru mu, marka rozeti doğru metni gösteriyor
      mu?
- [ ] `channels().list(mine=True)` ile OAuth token'ın doğru kanala
      bağlandığını doğrulayın (bkz. Adım 6.3).
- [ ] Gerçek bir test yüklemesi yapıp YouTube'da videonun doğru kanalda,
      doğru başlık/açıklama/etiketlerle göründüğünü kontrol edin.
- [ ] GitHub Actions sekmesinden ilgili workflow'u **workflow_dispatch**
      (manuel "Run workflow") ile bir kez tetikleyip CI ortamında da
      sorunsuz çalıştığını doğrulayın (lokal ortamda çalışması CI'da
      çalışacağının garantisi değildir — paket versiyonları, ffmpeg
      varlığı gibi farklar olabilir).
- [ ] `data/history_<profil-adi>.json`'ın gerçekten commit'lendiğini
      kontrol edin (workflow'un son adımı).

---

## 8. Zamanlama Stratejisi

Tüm kanalları aynı saat aralığına yığmak yerine, her kanalın hedef
kitlesinin GERÇEKTEN aktif olduğu saatlere yaymak daha iyi sonuç verir —
her kanal kendi bağımsız "ilk izlenme penceresini" yaşar, YouTube algoritması
karışmaz. Örnek (kullanılan) dağılım:

| Kanal türü | Önerilen saat (TR) | Mantık |
|---|---|---|
| Eğitim/pratik bilgi (kelime öğrenme vb.) | 08:00 | Güne başlarken, işe/okula giderken |
| Kısa bilgi/trivia | 12:30 | Öğle arası |
| Genel ilgi (tarih, kültür) | 18:30 | Eve dönüş saatleri |
| Sınav hazırlık (adaylar akşam çalışır) | 20:00–21:00 | Akşam ders çalışma saatleri |

Cron `UTC` bazlıdır, Türkiye UTC+3 — `cron: "0 17 * * *"` = 20:00 TR gibi
hesaplanır.

**İlk 30 gün saatleri değiştirmeyin** — YouTube'un o kanalın izleyici
kitlesini hangi saatlerde öne çıkaracağını öğrenmesi için düzenli bir yayın
takvimi önemlidir. Kanal büyüdükçe (izlenme verisi birikince) günde 2 video
modeline (sabah + akşam) geçmek düşünülebilir, ama önce tek video/gün ile
veri toplayıp organik olarak büyütmek daha sağlıklıdır.

---

## 9. GitHub Personal Access Token (PAT) Alma - cron-job.org İçin

**Neden Gerekli?**
- GitHub Actions'ın kendi cron zamanlayıcısı 2-9 saat gecikme yaşayabilir
- cron-job.org ile tam saatte tetiklemek için PAT şarttır
- PAT, dış servisin GitHub repo'nu tetiklemesine izin verir

**Adımlar:**
1. GitHub'da sağ üstteki profil resmine tıkla > **Settings** seç.
2. En soldaki menünün en altından **Developer settings**'e tıkla.
3. **Personal access tokens > Tokens (classic)** seçeneğine gir.
4. **Generate new token (classic)** de.
5. **Note:** `cron-job-token` yaz (bu sadece senin için bir etiket).
6. **Expiration:** `No expiration` (Süresiz) seç - token süresi dolarsa cron-job.org çalışmaz.
7. **İzinler (Scopes):** Sadece şu iki kutucuğu işaretle:
   - ✅ **repo** (repo'nun okunması/yazılması için)
   - ✅ **workflow** (workflow'ların tetiklenmesi için)
8. En alttan **Generate token** de.
9. `ghp_...` ile başlayan şifreyi kopyala ve güvenli bir yerde sakla.

**⚠️ ÖNEMLİ:**
- Bu token'ı asla GitHub'a commitleme (`.gitignore` dosyasında `client_secret.json` gibi)
- Token'ı sadece cron-job.org'da kullanacaksın
- Token çalınırsa hemen GitHub'dan sil ve yenisini oluştur

**cron-job.org'da Kullanımı:**
- URL: `https://api.github.com/repos/KULLANICI_ADIN/REPO_ADIN/actions/workflows/WORKFLOW_ADIN.yml/dispatches`
- Headers:
  - `Accept: application/vnd.github+json`
  - `Authorization: Bearer ghp_SENIN_TOKENIN` (Bearer kelimesinden sonra 1 boşluk var!)
- Body: `{"ref":"main"}`

---

## 10. Özet — Bir Cümlede

Tek bir Python kod tabanı + `profiles.py`'daki konfigürasyon + her kanal
için ayrı bir OAuth token/GitHub secret seti + ayrı bir GitHub Actions
workflow'u = sonsuz sayıda, birbirinden bağımsız, tamamen otonom YouTube
Shorts kanalı.
