"""Generates an original Turkish trivia/exam-prep question using the free Google Gemini API tier.

Which channel (KPSS, ehliyet, tarihte_bugun, ...) is controlled by the
CONTENT_PROFILE env var / profiles.py.
"""
import datetime
import json
import os
import random
import re
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from museum_source import fetch_random_object
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


_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "question": {"type": "STRING"},
        "answer": {"type": "STRING"},
        "explanation": {"type": "STRING"},
        "hashtags": {"type": "ARRAY", "items": {"type": "STRING"}},
    },
    "required": ["question", "answer", "explanation", "hashtags"],
}


def _generate_with_retry(client, prompt, max_attempts=3, delay_seconds=15):
    """Gemini's free tier occasionally returns a transient 503 ("high
    demand") even though the SDK already retries internally - we've hit this
    enough times to fail whole workflow runs, so retry a few more times with
    a delay before giving up for real."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_RESPONSE_SCHEMA,
                ),
            )
        except genai_errors.ServerError as e:
            last_error = e
            print(f"Gemini server error (attempt {attempt}/{max_attempts}): {e}")
            if attempt < max_attempts:
                time.sleep(delay_seconds)
    raise last_error


def _sanitize_hashtags(hashtags) -> list:
    if not isinstance(hashtags, list):
        return []
    cleaned = []
    for tag in hashtags:
        tag = normalize_text(str(tag))
        tag = re.sub(r"\s+", "", tag)
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = "#" + tag
        cleaned.append(tag)
    return cleaned[:5]


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

    if profile.get("is_story"):
        intro = f"Sen, İslam tarihi uzmanı ve {profile['topic_label']} anlatan, huzur veren, şefkatli bir anlatıcısın."
        task = f""""{category}" konusunda, sahih kaynaklara dayanan, etkileyici ve ders çıkarılabilecek
kısa BİR adet dini kıssa üret. Genel olarak bilinen, yaygın kabul gören bir olayı anlat;
kaynağı belirsiz veya tartışmalı rivayetlerden, uydurma ayrıntılardan kaçın.
Lütfen sistemin JSON formatını bozmadan şu yapıyı bir hikaye akışı gibi kullan:
- "question" alanına: Kıssanın girişini ve olayın gelişme kısmını sürükleyici ama KISA bir
  dille yaz (en fazla 3-4 cümle; soru olmak zorunda değil, olayı anlat). İLK CÜMLE bir
  merak unsuru veya çarpıcı bir an içermeli, izleyiciyi hemen içine çeksin; ASLA "Merhaba",
  "Bugün size..." gibi bir selamlama veya girizgahla başlama, direkt olayın içine gir.
- "answer" alanına: Olayın vurucu sonucunu 1 kısa cümleyle yaz.
- "explanation" alanına: "Kıssadan Hisse:" diyerek başlayıp, bu olaydan günümüzde
  çıkarmamız gereken ahlaki/dini dersi 2-3 KISA cümleyle (toplam en fazla ~220 karakter) yaz.
Sakin, ağırbaşlı ve samimi bir üslup kullan; abartılı/sansasyonel ifadelerden kaçın."""
    elif profile.get("is_myth_format"):
        intro = f"Sen, günlük YouTube Shorts {profile['topic_label']} kanalı için heyecanlı ve akıcı anlatan bir hikaye anlatıcısısın."
        task = f""""{category}" konusunda, çoğu insanın doğru sandığı ama aslında YANLIŞ olan,
yaygın BİR adet yanılgı/mit bul.
- "question" alanına, bu yanılgıyı 2 cümlelik, meraklandırıcı ve iddialı bir dille yaz
  (izleyiciye "evet bunu biliyorum" dedirtecek şekilde; örn. "Yarasalar tamamen kördür.
  Bu yüzden yönlerini bulmak için sadece sese güvenirler.")
- "answer" alanına, kısa ama vurgulu bir düzeltme cümlesi yaz (örn. "Hayır, yarasalar kör değildir!")
- "explanation" alanına, 3-4 KISA cümlelik (toplam en fazla ~220 karakter), akıcı ve
  ilgi çekici bir açıklama yaz: gerçek ne, şaşırtıcı bir detay veya örnek ver, ve bu
  yanılgının neden bu kadar yaygın olduğunu anlat. Uzun/karmaşık cümlelerden kaçın,
  ekranda okunacak kısa cümleler kullan. Konuşma diline yakın, samimi ve enerjik bir
  üslup kullan (gerektiğinde ünlem işareti kullanabilirsin).
Herkesin ilgisini çekecek, geniş kitleye hitap eden genel-kültür tarzı bir yanılgı seç;
kişisel/mahrem veya bazı izleyicileri rahatsız edebilecek beden/hijyen konularından kaçın."""
    elif profile.get("is_exam_prep", True):
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
ASCII karşılıklarıyla (i, g, u, s, o, c) değiştirme.
"hashtags" alanına, bu içeriğe özel (genel/sabit değil) 3-5 adet Türkçe hashtag üret;
her biri # ile başlasın, boşluk içermesin (örn. "#HzYusuf", "#SahraÇölü")."""

    response = _generate_with_retry(client, prompt)
    data = json.loads(response.text)
    # We already picked `category` ourselves (in Turkish); don't let the model
    # regenerate it, since it sometimes drifts into an English paraphrase.
    data["category"] = category

    required = {"category", "question", "answer", "explanation"}
    if not required.issubset(data):
        raise ValueError(f"Model response missing fields: {data!r}")

    for field in required:
        data[field] = normalize_text(str(data[field]))

    data["hashtags"] = _sanitize_hashtags(data.get("hashtags"))

    history["questions"].append(
        {
            "category": data["category"],
            "question": data["question"],
            "answer": data["answer"],
        }
    )
    save_history(history, history_path)

    return data


_MUSEUM_FORMAT_INSTRUCTIONS = {
    "TEK ESER": "Bu tek eserin hikayesini anlat: ne, kim tarafından, ne zaman yapıldı, neden önemli.",
    "ALTIN ÇAĞ": "Bu eserin ortaya çıktığı dönemin/medeniyetin altın çağını, o dönemin bilim/sanat/zanaat ortamını anlat.",
    "YÜZYILLARA MEYDAN OKUYAN": "Bu eserin nasıl yapıldığını, ne kadar dayanıklı olduğunu, bugüne nasıl ulaştığını anlat.",
    "BÖYLE ÖĞRENDİK": "Bu eserle/döneminle ilişkili bilim, ölçüm ya da keşif yöntemlerini anlat.",
}


def generate_museum_story(profile: dict, image_out_path: str, max_attempts: int = 3) -> dict:
    """Like generate_question(), but for the museum-object channel: fetches
    a real, catalogued public-domain artifact (photo + verified metadata)
    and has Gemini write ONLY from those given facts, instead of inventing
    a topic - this both avoids hallucination and gives us a genuine,
    correctly-licensed image to use as the video's background."""
    obj = None
    for _ in range(max_attempts):
        obj = fetch_random_object(image_out_path)
        if obj:
            break
    if not obj:
        raise RuntimeError("Could not find a suitable museum object after several attempts")

    format_name = random.choice(profile["categories"])
    facts = (
        f"Eser adı: {obj['title']}\n"
        f"Kültür/Dönem: {obj['culture']} {obj['period']} {obj['dynasty']}\n"
        f"Tarih: {obj['date']}\n"
        f"Sanatçı: {obj['artist'] or 'bilinmiyor'}\n"
        f"Malzeme: {obj['medium']}\n"
        f"Bölüm: {obj['department']}\n"
        f"Müze notu: {obj['description'] or obj['credit_line']}"
    )

    prompt = f"""Sen, müze eserlerinden yola çıkarak tarih hikayeleri anlatan, meraklı ve akıcı bir anlatıcısın.

Aşağıda GERÇEK bir müze eserinin doğrulanmış bilgileri var. SADECE bu bilgilere dayanarak,
uydurma detay eklemeden, "{format_name}" formatında bir hikaye yaz:
{_MUSEUM_FORMAT_INSTRUCTIONS[format_name]}

GERÇEK ESER BİLGİLERİ:
{facts}

- "question" alanına: Eserle ilgili merak uyandırıcı bir girişle başla (en fazla 3-4 cümle).
  ASLA "Merhaba" gibi bir selamlamayla başlama, direkt konunun içine gir.
- "answer" alanına: Vurucu bir sonuç/detay cümlesi yaz.
- "explanation" alanına: "Kısaca:" diyerek başlayıp 2-3 KISA cümleyle (toplam en fazla ~220 karakter) özetle.
Verilmeyen hiçbir bilgiyi (tarih, isim, olay) uydurma; bir alan hakkında yeterli bilgi yoksa
genel ama doğru ifadeler kullan, spesifik uydurma detay verme.
Sadece düz noktalama işaretleri kullan, markdown veya emoji kullanma. Türkçe yaz, Türkçe
karakterleri (ı, İ, ğ, ü, ş, ö, ç) doğru ve eksiksiz kullan.
"hashtags" alanına, bu içeriğe özel 3-5 adet Türkçe hashtag üret; her biri # ile başlasın,
boşluk içermesin."""

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
    response = _generate_with_retry(client, prompt)
    data = json.loads(response.text)
    data["category"] = format_name

    required = {"category", "question", "answer", "explanation"}
    if not required.issubset(data):
        raise ValueError(f"Model response missing fields: {data!r}")
    for field in required:
        data[field] = normalize_text(str(data[field]))
    data["hashtags"] = _sanitize_hashtags(data.get("hashtags"))
    data["source_credit"] = f"Görsel: {obj['museum']}, Kamu Malı (Public Domain) - {obj['title']}"
    return data


if __name__ == "__main__":
    import sys

    p = get_profile(sys.argv[1] if len(sys.argv) > 1 else None)
    q = generate_question(p)
    print(json.dumps(q, indent=2, ensure_ascii=False))
