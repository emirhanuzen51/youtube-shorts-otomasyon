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
