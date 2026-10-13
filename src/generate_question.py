"""Generates content using the free Google Gemini API tier.

Which channel (dogru_bilinen_yanlislar, dini_kissalar, muze_sirlari, uzayin_sirlari) is controlled by the
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
from nasa_source import fetch_random_nasa_item
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
        "image_query": {"type": "STRING"},
        "reveal_image_query": {"type": "STRING"},
    },
    "required": ["question", "answer", "explanation", "hashtags"],
}


def _generate_with_retry(client, prompt, max_attempts=4, delay_seconds=20):
    """Gemini's free tier occasionally returns a transient 503 ("high
    demand") even though the SDK already retries internally - we've hit this
    enough times to fail whole workflow runs, so retry a few more times with
    a growing delay before giving up for real. A demand spike can outlast a
    short retry burst, so this backs off (20s, 40s, 60s...) to spread attempts
    over a couple minutes. Kept deliberately modest (not higher): the free
    tier's daily quota is only 20 requests/day total, and each retry attempt
    here is itself a metered request - retrying too aggressively on a single
    generation can burn through the whole day's budget by itself. A 429
    (quota exhausted) isn't a ServerError so it isn't caught/retried here -
    retrying it would just fail identically and waste more quota."""
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
                time.sleep(delay_seconds * attempt)
                continue
            raise last_error
    raise last_error


_TR_CHARS = set("ığşöüçİĞŞÖÜÇ")


def _missing_turkish_chars(*texts) -> bool:
    """Gemini occasionally drifts into writing Turkish sentences with the
    diacritics stripped entirely (e.g. "doneminde" instead of "döneminde") -
    a different failure mode than the NFD-decomposition bug normalize_text
    already fixes, and not something sanitization can repair after the fact
    since the information is just gone. A genuine Turkish text of any real
    length is overwhelmingly likely to contain at least one ığşöüçİĞŞÖÜÇ, so
    its total absence is a reliable signal to just regenerate."""
    combined = "".join(texts)
    return len(combined) > 60 and not any(ch in _TR_CHARS for ch in combined)


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
- "question" alanına: İlk 2-3 saniyede izleyiciyi ekrana kilitleyecek şok edici bir kanca (Hook) ile başla. Bu yanılgıyı 2 cümlelik, meraklandırıcı ve iddialı bir dille yaz (izleyiciye "evet ben de böyle biliyordum" dedirtecek şekilde).
- "answer" alanına: Kısa, enerjik ve tokat gibi çarpan net bir düzeltme cümlesi yaz (örn. "Hayır, yarasalar kör değildir!").
- "explanation" alanına: 3-4 KISA cümlelik (toplam ~180-220 karakter), aşırı akıcı bir açıklama yaz: gerçek ne, şaşırtıcı detay ne ve neden yanlış biliniyor.
- SONSUZ DÖNGÜ (Infinite Loop) KURALI: "explanation" alanının en son cümlesini, videonun başındaki kancaya pürüzsüz bağlanabilecek bir geçişle bitir (örn. "...işte tam da bu yüzden herkes şunu sanıyor:"). Böylece video başa sardığında izleyici fark etmeden 2. kez izlesin!
Herkesin ilgisini çekecek, geniş kitleye hitap eden genel-kültür tarzı bir yanılgı seç;
kişisel/mahrem konulardan kaçın."""
    elif profile.get("is_exam_prep", True):
        intro = f"Sen, günlük YouTube Shorts {profile['topic_label']} hazırlık kanalı için soru yazan bir eğitmensin."
        task = f""""{category}" konusunda, {profile['topic_label']} tarzında, özgün BİR adet deneme sorusu üret.
Bu gerçek bir sınavda çıkmış soru DEĞİL, sınav formatına ve zorluk seviyesine uygun,
senin ürettiğin doğru ve güncel bilgilere dayanan orijinal bir deneme sorusu olmalı."""
    else:
        intro = f"Sen, günlük YouTube Shorts {profile['topic_label']} kanalı için içerik yazan bir eğitmensin."
        task = f""""{category}" konusunda, ilgi çekici ve bilgilendirici BİR adet trivia sorusu üret."""

    image_instruction = ""
    if profile.get("use_topic_image"):
        image_instruction = (
            "\n\"image_query\" alanına: Soruda geçen yanılgının/konunun somut görselini "
            "1-3 kelimelik İNGİLİZCE bir stok-fotoğraf arama terimi olarak yaz (örn. \"housefly close up\").\n"
            "\"reveal_image_query\" alanına: Cevap/açıklama sahnesinde ekrana gelecek GERÇEK kanıtı "
            "veya doğrulayıcı farklı bir açıyı 1-3 kelimelik İNGİLİZCE arama terimi olarak yaz "
            "(örn. \"microscope fly head\" veya \"fly flying slow motion\").\n"
        )

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
her biri # ile başlasın, boşluk içermesin (örn. "#HzYusuf", "#SahraÇölü").
{image_instruction}"""

    required = {"category", "question", "answer", "explanation"}
    data = None
    for attempt in range(1, 4):
        response = _generate_with_retry(client, prompt)
        candidate = json.loads(response.text)
        # We already picked `category` ourselves (in Turkish); don't let the
        # model regenerate it, since it sometimes drifts into an English paraphrase.
        candidate["category"] = category
        if not required.issubset(candidate):
            raise ValueError(f"Model response missing fields: {candidate!r}")
        for field in required:
            candidate[field] = normalize_text(str(candidate[field]))
        if _missing_turkish_chars(candidate["question"], candidate["answer"], candidate["explanation"]):
            print(f"Generated text is missing Turkish characters (attempt {attempt}/3), retrying...")
            continue
        data = candidate
        break
    if data is None:
        raise ValueError("Model kept generating text without Turkish characters after 3 attempts")

    data["hashtags"] = _sanitize_hashtags(data.get("hashtags"))
    if data.get("image_query"):
        data["image_query"] = normalize_text(str(data["image_query"]))
    if data.get("reveal_image_query"):
        data["reveal_image_query"] = normalize_text(str(data["reveal_image_query"]))

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

- "question" alanına: İlk 2 saniyede izleyiciyi ekrana kilitleyecek merak uyandırıcı bir kanca (Hook) ile başla; eserin adını ("{obj['title']}") doğal şekilde geçirerek konunun tam içine gir (toplam en fazla 2-3 kısa cümle). ASLA selamlama ile başlama.
- "answer" alanına: Vurucu, şaşırtıcı bir sonuç/detay cümlesi yaz.
- "explanation" alanına: 2-3 KISA cümleyle (toplam ~180-220 karakter) eserin en gizemli veya büyüleyici yanını özetle.
- SONSUZ DÖNGÜ (Infinite Loop) KURALI: "explanation" kısmının son cümlesini videonun başına akıcı bağlayacak bir köprüyle bitir (örn. "...işte bu gizem bizi şu soruya götürüyor:"). Böylece video kesintisiz döngüye girsin!
Verilmeyen hiçbir bilgiyi (tarih, isim, olay) uydurma; bir alan hakkında yeterli bilgi yoksa
genel ama doğru ifadeler kullan, spesifik uydurma detay verme.
Sadece düz noktalama işaretleri kullan, markdown veya emoji kullanma. Türkçe yaz, Türkçe
karakterleri (ı, İ, ğ, ü, ş, ö, ç) doğru ve eksiksiz kullan; bunları ASCII karşılıklarıyla
(i, g, u, s, o, c) DEĞİŞTİRME - bu çok önemli, her Türkçe karakter doğru yazılmalı.
"hashtags" alanına, bu içeriğe özel 3-5 adet Türkçe hashtag üret; her biri # ile başlasın,
boşluk içermesin."""

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    required = {"category", "question", "answer", "explanation"}
    data = None
    for attempt in range(1, 4):
        response = _generate_with_retry(client, prompt)
        candidate = json.loads(response.text)
        candidate["category"] = format_name
        if not required.issubset(candidate):
            raise ValueError(f"Model response missing fields: {candidate!r}")
        for field in required:
            candidate[field] = normalize_text(str(candidate[field]))
        if _missing_turkish_chars(candidate["question"], candidate["answer"], candidate["explanation"]):
            print(f"Generated text is missing Turkish characters (attempt {attempt}/3), retrying...")
            continue
        data = candidate
        break
    if data is None:
        raise ValueError("Model kept generating text without Turkish characters after 3 attempts")
    data["hashtags"] = _sanitize_hashtags(data.get("hashtags"))
    data["source_credit"] = f"Görsel: {obj['museum']}, Kamu Malı (Public Domain) - {obj['title']}"
    return data


_NASA_FORMAT_INSTRUCTIONS = {
    "GÖRDÜĞÜN GERÇEK": "Görüntüde tam olarak ne olduğunu, neyin nasıl oluştuğunu çarpıcı bir dille anlat.",
    "DEV RAKAMLAR": "Bu gök cismi/olayla ilgili büyüklük, mesafe, sıcaklık gibi akıl almaz bir ölçeği vurgula.",
    "NASA'NIN GÖZÜYLE": "Bu görüntünün hangi görev/teleskop/araçla, nasıl elde edildiğini anlat.",
    "EVRENİN DERİNLİĞİ": "Bu nesnenin evrendeki yerini, ne kadar uzakta/eski olduğunu merak uyandırıcı şekilde anlat.",
}


def generate_nasa_story(profile: dict, image_out_path: str, max_attempts: int = 3) -> dict:
    """Like generate_museum_story(), but for the space-imagery channel:
    fetches a real NASA-captioned image (public domain) and has Gemini
    write ONLY from those given facts, instead of inventing a topic."""
    obj = None
    for _ in range(max_attempts):
        obj = fetch_random_nasa_item(image_out_path)
        if obj:
            break
    if not obj:
        raise RuntimeError("Could not find a suitable NASA item after several attempts")

    format_name = random.choice(profile["categories"])
    facts = (
        f"Başlık: {obj['title']}\n"
        f"NASA açıklaması: {obj['description']}\n"
        f"Tarih: {obj['date_created']}\n"
        f"NASA merkezi: {obj['center']}\n"
        f"Anahtar kelimeler: {obj['keywords']}"
    )

    prompt = f"""Sen, NASA'nın gerçek uzay görüntülerinden yola çıkarak evren hikayeleri anlatan, meraklı ve akıcı bir anlatıcısın.

Aşağıda GERÇEK bir NASA görüntüsünün doğrulanmış bilgileri var. SADECE bu bilgilere dayanarak,
uydurma detay eklemeden, "{format_name}" formatında bir hikaye yaz:
{_NASA_FORMAT_INSTRUCTIONS[format_name]}

GERÇEK NASA BİLGİLERİ:
{facts}

- "question" alanına: İlk 2 saniyede izleyiciyi şaşırtacak merak uyandırıcı bir kanca (Hook) ile başla; görüntünün/nesnenin adını ("{obj['title']}") geçirerek konunun tam içine gir (toplam en fazla 2-3 cümle). ASLA selamlama ile başlama.
- "answer" alanına: Vurucu, akıl almaz bir sonuç/ölçek cümlesi yaz.
- "explanation" alanına: 2-3 KISA cümleyle (toplam ~180-220 karakter) bu uzay olayının en çarpıcı yönünü özetle.
- SONSUZ DÖNGÜ (Infinite Loop) KURALI: "explanation" kısmının en son cümlesini videonun başındaki kancaya pürüzsüz bağlanacak bir köprüyle bitir (örn. "...işte tam da bu yüzden bilim insanları şunu merak ediyor:"). Böylece video başa sardığında izleyici 2. tura geçsin!
Verilmeyen hiçbir bilgiyi (rakam, tarih, isim) uydurma; bir alan hakkında yeterli bilgi yoksa
genel ama doğru ifadeler kullan, spesifik uydurma detay verme.
Sadece düz noktalama işaretleri kullan, markdown veya emoji kullanma. Türkçe yaz, Türkçe
karakterleri (ı, İ, ğ, ü, ş, ö, ç) doğru ve eksiksiz kullan; bunları ASCII karşılıklarıyla
(i, g, u, s, o, c) DEĞİŞTİRME - bu çok önemli, her Türkçe karakter doğru yazılmalı.
"hashtags" alanına, bu içeriğe özel 3-5 adet Türkçe hashtag üret; her biri # ile başlasın,
boşluk içermesin."""

    api_key = os.environ["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)

    required = {"category", "question", "answer", "explanation"}
    data = None
    for attempt in range(1, 4):
        response = _generate_with_retry(client, prompt)
        candidate = json.loads(response.text)
        candidate["category"] = format_name
        if not required.issubset(candidate):
            raise ValueError(f"Model response missing fields: {candidate!r}")
        for field in required:
            candidate[field] = normalize_text(str(candidate[field]))
        if _missing_turkish_chars(candidate["question"], candidate["answer"], candidate["explanation"]):
            print(f"Generated text is missing Turkish characters (attempt {attempt}/3), retrying...")
            continue
        data = candidate
        break
    if data is None:
        raise ValueError("Model kept generating text without Turkish characters after 3 attempts")
    data["hashtags"] = _sanitize_hashtags(data.get("hashtags"))
    data["source_credit"] = f"Görsel: NASA, Kamu Malı (Public Domain) - {obj['title']}"
    return data


if __name__ == "__main__":
    import sys

    p = get_profile(sys.argv[1] if len(sys.argv) > 1 else None)
    q = generate_question(p)
    print(json.dumps(q, indent=2, ensure_ascii=False))
