"""Per-channel content configuration. Add a new dict here to spin up another
channel on the same codebase - everything else (TTS, rendering, upload,
scheduling) is shared.
"""
import os

PROFILES = {
    "dogru_bilinen_yanlislar": {
        "is_exam_prep": False,
        "is_myth_format": True,
        "use_topic_image": True,
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
        "music_enabled": False,
        "accent_color": "#FF5A36",
        "reveal_rect_color": [90, 12, 12],
        "reveal_tint": [130, 20, 20],
        "guess_prompt": "Sen de mi öyle biliyordun?",
        "reveal_label": "YANLIŞ BİLİYORSUN!",
        "question_intro": "Çoğu insan bunun doğru olduğunu düşünür.",
        "answer_intro": "Ama hayır! Gerçek şu ki,",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir yanılgı!",
        "comment_cta": "Sen de bu şekilde mi biliyordun? Dürüstçe yoruma yaz! 👇",
        "title_hashtags": "#Shorts #Trending #YanlışBilinenDoğrular",
        "description_hashtags": "#Shorts #Viral #Trending #DoğruBilinenYanlışlar #Mit #YanlışBilinenDoğrular #GenelKültür #BilgiVideosu",
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
        "comment_cta": "Bu kıssadan çıkardığın en büyük hisse ne oldu? Yorumlarda buluşalım 👇",
        "title_hashtags": "#Shorts #DiniKıssalar #İslam #İbretlik",
        "description_hashtags": "#Shorts #Viral #DiniKıssalar #İbretlikHikayeler #İslamTarihi #Peygamberler #KıssadanHisse #Maneviyat",
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
        "comment_cta": "Sence bu eserin arkasındaki en büyük gizem ne olabilir? Fikrini yaz 👇",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir sır!",
        "title_hashtags": "#Shorts #Müze #Tarih #Arkeoloji",
        "description_hashtags": "#Shorts #Viral #MüzeSırları #Tarih #ArkeolojiTarihi #SanatTarihi #Medeniyet #GizemliOlaylar",
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
    "uzayin_sirlari": {
        "is_exam_prep": False,
        "is_nasa_object": True,
        "music_enabled": False,
        # 4 rotasyonlu format ismi - generate_nasa_story() bunlardan birini
        # rastgele secip Gemini'ye gercek NASA gorsel/verisine dayanarak o
        # formatta yazdirir. "category" olarak kullanildigi icin rozette de
        # gorunur.
        "categories": ["GÖRDÜĞÜN GERÇEK", "DEV RAKAMLAR", "NASA'NIN GÖZÜYLE", "EVRENİN DERİNLİĞİ"],
        "history_file": "history_uzayin_sirlari.json",
        "video_badge": "UZAYIN SIRLARI",
        "guess_prompt": "Merak ediyor musun?",
        "reveal_label": "SONUÇ",
        "answer_intro": "",
        "voice": "tr-TR-AhmetNeural",
        # Uzay temasi: derin lacivert-siyah zemin, elektrik mavisi/mor glow -
        # diger kanallardaki bronz/yesil/kirmizi/mor temalardan ayri bir
        # kimlik. Arka plan zaten gercek NASA fotografi oldugu icin bu
        # renkler sadece foto yuklenemezse yedek gradyan olarak kullanilir.
        "bg_top": [5, 8, 25],
        "bg_bottom": [10, 5, 20],
        "bg_glow_top": [20, 40, 90],
        "bg_glow_bottom": [60, 20, 90],
        "badge_bg": "#3DA9FC",
        "badge_fg": "#03081A",
        "accent_color": "#3DA9FC",
        "reveal_rect_color": [10, 15, 45],
        "reveal_tint": [20, 30, 70],
        "comment_cta": "Sence evrende yalnız mıyız? Bu görüntü hakkındaki düşünceni yoruma bırak 👇",
        "outro_line1": "Takip et,",
        "outro_line2": "her gün yeni bir uzay sırrı!",
        "title_hashtags": "#Shorts #Uzay #NASA #Astronomi",
        "description_hashtags": "#Shorts #Viral #Trending #UzayınSırları #NASA #Astronomi #Evren #Uzay #KaraDelik",
        "tags": ["uzay", "nasa", "astronomi", "evren", "gezegenler", "galaksi"],
        "banner_title": "UZAYIN SIRLARI",
        "banner_tagline": "Her gün NASA'nın gerçek görüntülerinden bir uzay sırrı",
        "profile_pic_text": "UZAY",
        "channel_description": """Her gün NASA'nın gerçek, halka açık görüntülerinden bir uzay sırrı!

NASA'nın açık erişim kütüphanesindeki gerçek fotoğraf ve verilerden yola \
çıkarak kara delikleri, galaksileri, gezegenleri ve uzay görevlerini \
anlatıyoruz. Kullanılan görseller kamu malı (public domain) NASA \
fotoğraflarıdır.

Abone olun, her gün yeni bir uzay sırrında buluşalım.

#UzayınSırları #NASA #Astronomi
""",
    },
}


def get_profile(name: str | None = None) -> dict:
    name = name or os.environ.get("CONTENT_PROFILE", "dogru_bilinen_yanlislar")
    if name not in PROFILES:
        raise ValueError(f"Unknown CONTENT_PROFILE {name!r}. Choose from: {list(PROFILES)}")
    return {"name": name, **PROFILES[name]}
