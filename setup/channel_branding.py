"""One-time script to generate channel branding assets (banner + profile picture)
and push the banner + description to a YouTube channel via the API.

The YouTube Data API has no endpoint to set the channel profile picture/avatar,
so that PNG is generated locally and must be uploaded manually in YouTube Studio
(Channel customization -> Branding -> Picture -> Upload).

Usage (from the project root), credentials for the TARGET channel:
    YT_CLIENT_ID=... YT_CLIENT_SECRET=... YT_REFRESH_TOKEN=... \
        python setup/channel_branding.py <profile-name>

<profile-name> is one of the keys in src/profiles.py (e.g. dogru_bilinen_yanlislar, dini_kissalar).
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
