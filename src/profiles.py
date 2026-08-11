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
    "dogru_bilinen_yanlislar": {
        "is_exam_prep": False,
        "is_myth_format": True,
        # Hayvanlar/bilim/uzay biraz agirlikli (ilgi cekici, herkese hitap eden
        # konular) ama liste genel olarak dengeli - tek bir dar konuya
        # sikismasin diye "sağlık ve beden mitleri" gibi kisisel hissedilebilecek
        # kategoriler de var olmakla birlikte agirliklandirilmadi.
        "categories": [
            "hayvanlar hakkında yanlış bilgiler", "hayvanlar hakkında yanlış bilgiler",
            "bilim ve doğa yanılgıları", "bilim ve doğa yanılgıları",
            "uzay ve evren yanılgıları",
            "tarih yanılgıları",
            "coğrafya ve dünya yanılgıları",
            "gündelik hayat mitleri",
            "dil ve kelime yanılgıları",
            "sağlık ve beden mitleri",
        ],
        "topic_label": "yaygın bilgi yanılgıları (mitler)",
        "history_file": "history_dogru_bilinen_yanlislar.json",
        "video_badge": "DOĞRU MU YANLIŞ MI?",
        # Mit-cozme konseptine ozel tema: soru ekrani koyu/gizemli lacivert-mor,
        # rozet ve vurgular alarm kirmizisi, reveal ekrani (diger kanallardaki
        # "dogru cevap" yesili yerine) "YANLIŞ!" hissini veren kirmizi/bordo.
        "bg_top": [8, 8, 22],
        "bg_bottom": [45, 8, 18],
        "bg_glow_top": [70, 8, 30],
        "bg_glow_bottom": [30, 6, 45],
        "badge_bg": "#FF3B3B",
        "badge_fg": "#FFFFFF",
        "music_file": "starostin-shorts-youtube-shorts-background-music-261844.mp3",
        "accent_color": "#FF5A36",
        "reveal_rect_color": [90, 12, 12],
        "reveal_tint": [130, 20, 20],
        "guess_prompt": "Sen de mi öyle biliyordun?",
        "reveal_label": "YANLIŞ BİLİYORSUN!",
        "question_intro": "Çoğu insan bunun doğru olduğunu düşünür.",
        "answer_intro": "Ama hayır! Gerçek şu ki,",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir yanılgı!",
        "title_hashtags": "#Shorts #YanlışBilinenDoğrular",
        "description_hashtags": "#Shorts #DoğruBilinenYanlışlar #Mit #YanlışBilinenDoğrular #GenelKultur #BilgiVideosu",
        "tags": ["yanlis bilinen dogrular", "dogru bilinen yanlislar", "mit", "sehir efsanesi", "genel kultur"],
        "banner_title": "DOĞRU BİLİNEN YANLIŞLAR",
        "banner_tagline": "Herkesin yanıldığı bilgiler, her gün bir tane",
        "profile_pic_text": "YANLIŞ",
        "channel_description": """Herkesin doğru sandığı ama aslında yanlış olan bilgiler!

Bilim, tarih, sağlık, hayvanlar ve gündelik hayattan yaygın yanılgıları \
her gün bir tane çürütüyoruz. Önce sen de "doğru" san, sonra gerçeği öğren.

Kaçırmamak için abone ol, her gün seninleyiz!

#DoğruBilinenYanlışlar #Mit #GenelKultur
""",
    },
    "dini_kissalar": {
        "is_exam_prep": False,
        "is_story": True,
        "categories": [
            "Peygamber Efendimiz'in (S.A.V) hayatından merhamet örnekleri",
            "Kur'an-ı Kerim'de adı geçen peygamberlerin kıssaları",
            "Sahabelerin hayatından sadakat ve doğruluk örnekleri",
            "İslam tarihinde sabır ve şükür konulu yaşanmış olaylar",
            "Gündelik hayata uyarlanabilecek ahlaki ve dini hikayeler",
        ],
        "topic_label": "dini kıssalar ve ibretlik hikayeler",
        "history_file": "history_dini_kissalar.json",
        "video_badge": "GÜNÜN KISSASI",
        "guess_prompt": "Kıssadan hisse nedir?",
        "reveal_label": "SONUÇ",
        "answer_intro": "İşte sonuç:",
        "voice": "tr-TR-AhmetNeural",
        "music_volume": 0.3,
        "music_file": "Ney-Gel-Gor-Beni-Ask-Neyledi-Ney-Dinle.mp3",
        # Islam sanatina uygun koyu yesil + altin/zeytin tonlari (diger
        # kanallardaki mor/lacivert ve kirmizi temalardan farkli kimlik).
        "bg_top": [10, 35, 24],
        "bg_bottom": [8, 20, 14],
        "bg_glow_top": [40, 70, 35],
        "bg_glow_bottom": [55, 45, 15],
        "badge_bg": "#D4AF37",
        "badge_fg": "#0B1A10",
        "accent_color": "#D4AF37",
        "reveal_rect_color": [12, 30, 20],
        "reveal_tint": [20, 45, 28],
        "outro_line1": "Daha fazla kıssa için",
        "outro_line2": "kanalımızı takip et!",
        "title_hashtags": "#Shorts #DiniKıssalar #İslam",
        "description_hashtags": "#Shorts #DiniKıssalar #İbretlikHikayeler #İslamTarihi #Peygamberler #KıssadanHisse",
        "tags": ["dini hikayeler", "kıssalar", "islam tarihi", "peygamberlerin hayatı", "dini sohbet"],
        "banner_title": "GÜNÜN KISSASI",
        "banner_tagline": "Her gün kalplere dokunan ibretlik bir kıssa",
        "profile_pic_text": "KISSA",
        "channel_description": """Her gün kalplere dokunan, maneviyatınızı güçlendirecek ibretlik bir dini kıssa!

Peygamber Efendimiz (S.A.V), diğer peygamberler ve sahabelerin hayatından \
ders çıkarılabilecek hikayeleri sizlerle paylaşıyoruz.

Not: Bu kanaldaki anlatımlar yapay zeka desteğiyle derlenmiştir; dini bir \
fetva veya birebir kaynak niteliği taşımaz. Doğrulama için orijinal \
kaynaklara başvurmanızı tavsiye ederiz.

Abone olun, her gün yeni bir hikayede buluşalım.

#DiniKıssalar #İbretlikHikayeler #İslamTarihi
""",
    },
    "muze_sirlari": {
        "is_exam_prep": False,
        "is_museum_object": True,
        # 4 rotasyonlu format ismi - generate_museum_story() bunlardan birini
        # rastgele secip Gemini'ye gercek muze verisine dayanarak o formatta
        # yazdirir. "category" olarak kullanildigi icin de rozette gorunur.
        "categories": ["TEK ESER", "ALTIN ÇAĞ", "YÜZYILLARA MEYDAN OKUYAN", "BÖYLE ÖĞRENDİK"],
        "history_file": "history_muze_sirlari.json",
        "video_badge": "MÜZE SIRLARI",
        "guess_prompt": "Merak ediyor musun?",
        "reveal_label": "SONUÇ",
        "answer_intro": "",
        "voice": "tr-TR-AhmetNeural",
        # Antika/muze havasi: sicak bronz-altin tonlari, diger kanallardaki
        # yesil/kirmizi/mor temalardan ayri bir kimlik. Arka plan zaten
        # gercek muze fotografi oldugu icin bu renkler sadece foto
        # yuklenemezse yedek gradyan olarak kullanilir.
        "bg_top": [35, 25, 15],
        "bg_bottom": [15, 10, 8],
        "bg_glow_top": [90, 60, 20],
        "bg_glow_bottom": [50, 30, 10],
        "badge_bg": "#D4A017",
        "badge_fg": "#1A1208",
        "accent_color": "#D4A017",
        "reveal_rect_color": [40, 25, 10],
        "reveal_tint": [60, 40, 15],
        "comment_cta": "Bu eser hakkında ne düşünüyorsun? Yorumlarda paylaş 👇",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir sır!",
        "title_hashtags": "#Shorts #Müze #Tarih",
        "description_hashtags": "#Shorts #MüzeSırları #Tarih #ArkeolojiTarihi #SanatTarihi #Medeniyet",
        "tags": ["muze", "tarih", "arkeoloji", "sanat tarihi", "eski medeniyetler", "tarihi eserler"],
        "banner_title": "MÜZE SIRLARI",
        "banner_tagline": "Her gün dünya müzelerinden gerçek bir eser, gerçek bir hikaye",
        "profile_pic_text": "MÜZE",
        "channel_description": """Her gün dünya müzelerinden gerçek bir eser, gerçek bir hikaye!

Met Museum'un halka açık koleksiyonundaki gerçek, katalog kayıtlı eserlerden \
yola çıkarak eski medeniyetlerin, sanatın ve zanaatın hikayelerini anlatıyoruz. \
Kullanılan görseller kamu malı (public domain) müze fotoğraflarıdır.

Abone olun, her gün yeni bir eserde buluşalım.

#MüzeSırları #Tarih #SanatTarihi
""",
    },
}


def get_profile(name: str | None = None) -> dict:
    name = name or os.environ.get("CONTENT_PROFILE", "kpss")
    if name not in PROFILES:
        raise ValueError(f"Unknown CONTENT_PROFILE {name!r}. Choose from: {list(PROFILES)}")
    return {"name": name, **PROFILES[name]}
