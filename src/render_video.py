"""Renders a 1080x1920 Shorts video for a trivia question using PIL + MoviePy.

No stock footage is used (avoids licensing issues and external downloads that
could fail in CI): the background is a procedurally generated animated gradient.
"""
import math
import os
import random
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_audioclips
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

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
_BG_GLOW_TOP = np.array([60, 10, 90])
_BG_GLOW_BOTTOM = np.array([10, 40, 110])


def _gradient_frame(t: float, bg_top=_BG_TOP, bg_bottom=_BG_BOTTOM, glow_top=_BG_GLOW_TOP, glow_bottom=_BG_GLOW_BOTTOM) -> np.ndarray:
    """Vertical gradient with a slow animated hue-shifting glow."""
    shift = (math.sin(t * 0.5) + 1) / 2  # 0..1
    top = bg_top * (1 - shift * 0.3) + glow_top * (shift * 0.3)
    bottom = bg_bottom * (1 - shift * 0.3) + glow_bottom * (shift * 0.3)

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
    so long questions/answers never overflow into neighboring elements.
    `max_lines` is a hard guarantee: if the text is still too long once the
    font hits min_font, it gets truncated with an ellipsis rather than left
    to overflow and overlap whatever is drawn below it."""
    font_size = max_font
    wrap_width = base_wrap
    lines = _wrap(text, wrap_width)
    while len(lines) > max_lines and font_size > min_font:
        font_size -= step_font
        wrap_width += step_wrap
        lines = _wrap(text, wrap_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;:-") + "..."
    return _font(font_size), lines


def _badge(draw, text, cy, font, fg="#0B0B14", bg="#FFD400"):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 36, 18
    box_w, box_h = tw + pad_x * 2, th + pad_y * 2
    x0 = (W - box_w) / 2
    y0 = cy - box_h / 2
    draw.rounded_rectangle([x0, y0, x0 + box_w, y0 + box_h], radius=box_h / 2, fill=bg)
    draw.text((W / 2 - tw / 2, y0 + pad_y - bbox[1]), text, font=font, fill=fg)


_BAND_COLOR = np.array([6, 6, 14], dtype=np.float32)


def _band(img, top, bottom, opacity=140):
    """Draws a translucent dark band behind a text region for readability
    against the busy animated gradient background. Returns a new RGB image.
    Blends directly on the numpy array (cheap) instead of PIL alpha_composite
    (expensive full-image RGBA round-trip), since this runs every frame."""
    top_c, bottom_c = max(0, int(top)), min(H, int(bottom))
    if bottom_c <= top_c:
        return img
    arr = np.array(img, dtype=np.float32)
    alpha = opacity / 255.0
    arr[top_c:bottom_c, :, :] = arr[top_c:bottom_c, :, :] * (1 - alpha) + _BAND_COLOR * alpha
    return Image.fromarray(arr.astype(np.uint8))


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
    font_outro = _font(56)
    font_countdown = _font(140)

    # Theme: profile-configurable so each channel can look distinct while
    # sharing the same render pipeline (defaults match the original look).
    accent = profile.get("accent_color", "#FFD400")
    badge_bg = profile.get("badge_bg", "#FFD400")
    badge_fg = profile.get("badge_fg", "#0B0B14")
    bg_top = np.array(profile.get("bg_top", [20, 16, 60]))
    bg_bottom = np.array(profile.get("bg_bottom", [90, 20, 120]))
    glow_top = np.array(profile.get("bg_glow_top", [60, 10, 90]))
    glow_bottom = np.array(profile.get("bg_glow_bottom", [10, 40, 110]))
    reveal_rect_color = tuple(profile.get("reveal_rect_color", (10, 90, 40)))
    reveal_tint = np.array(profile.get("reveal_tint", [15, 90, 45]))

    _measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    font_q, q_lines = _fit_text(question["question"], max_font=64, min_font=38, base_wrap=22, max_lines=6)
    _, q_block_h = _block_metrics(_measure_draw, q_lines, font_q, stroke_width=8)

    font_answer, a_lines = _fit_text(question["answer"], max_font=72, min_font=40, base_wrap=16, max_lines=4)
    _, a_block_h = _block_metrics(_measure_draw, a_lines, font_answer, stroke_width=8)

    font_explain, exp_lines = _fit_text(question["explanation"], max_font=42, min_font=26, base_wrap=30, max_lines=9)
    _, exp_block_h = _block_metrics(_measure_draw, exp_lines, font_explain, stroke_width=5, line_spacing=1.3)

    def make_frame(t):
        bg = _gradient_frame(t, bg_top, bg_bottom, glow_top, glow_bottom)
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        if t < INTRO_DUR:
            p = _ease_out(min(t / 0.6, 1.0))
            alpha_badge_y = H * 0.42 + (1 - p) * 40
            _badge(draw, profile["video_badge"], alpha_badge_y, font_badge, fg=badge_fg, bg=badge_bg)
            if t > 0.6:
                p2 = _ease_out(min((t - 0.6) / 0.6, 1.0))
                cat_text = question["category"].upper()
                draw.text(
                    (W / 2, H * 0.55 + (1 - p2) * 30), cat_text,
                    font=font_answer_label, fill=(255, 255, 255, int(255 * p2)),
                    anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0),
                )

        elif t < countdown_start:
            p = _ease_out(min((t - INTRO_DUR) / QUESTION_IN_DUR, 1.0))
            block_top = H * 0.26 + (1 - p) * 30
            guess_y = min(max(H * 0.62, block_top + q_block_h + 70), H * 0.85)
            img = _band(img, block_top - 30, guess_y + 55)
            draw = ImageDraw.Draw(img)
            _badge(draw, question["category"].upper(), H * 0.14, font_badge, fg=badge_fg, bg=badge_bg)
            _draw_text_block(
                draw, q_lines, font_q, W / 2, block_top + q_block_h / 2,
                fill="#FFFFFF", stroke_fill="#000000", stroke_width=8,
            )
            draw.text((W / 2, guess_y), profile["guess_prompt"], font=font_answer_label,
                       fill=accent, anchor="mm", stroke_width=3, stroke_fill="#000000")

        elif t < reveal_start:
            block_top = H * 0.20
            img = _band(img, block_top - 30, block_top + q_block_h + 30)
            draw = ImageDraw.Draw(img)
            _badge(draw, question["category"].upper(), H * 0.14, font_badge, fg=badge_fg, bg=badge_bg)
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
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=accent, width=10)
            draw.text((cx, cy), str(count_val), font=font_countdown, fill=accent,
                       anchor="mm", stroke_width=4, stroke_fill="#000000")

        elif t < outro_start:
            p = _ease_out(min((t - countdown_end) / REVEAL_IN_DUR, 1.0))
            draw.rectangle([0, 0, W, H], fill=reveal_rect_color)
            bg2 = _gradient_frame(t, bg_top, bg_bottom, glow_top, glow_bottom)
            blended = (np.array(bg2, dtype=float) * 0.25 + reveal_tint.astype(float) * 0.75).astype(np.uint8)
            img = Image.fromarray(blended)

            label_y = H * 0.16 + (1 - p) * 20
            answer_top = H * 0.24 + (1 - p) * 20
            show_exp = t > reveal_start + 0.3
            exp_y = None
            if show_exp:
                exp_top_min = answer_top + a_block_h + 70
                exp_y = min(max(H * 0.52, exp_top_min + exp_block_h / 2), H * 0.94 - exp_block_h / 2)
                band_bottom = exp_y + exp_block_h / 2 + 30
            else:
                band_bottom = answer_top + a_block_h + 30
            img = _band(img, label_y - 45, band_bottom)
            draw = ImageDraw.Draw(img)

            draw.text((W / 2, label_y), profile.get("reveal_label", "CEVAP"), font=font_answer_label,
                       fill="#FFFFFF", anchor="mm", stroke_width=3, stroke_fill="#000000")
            _draw_text_block(
                draw, a_lines, font_answer, W / 2, answer_top + a_block_h / 2,
                fill=accent, stroke_fill="#000000", stroke_width=8,
            )
            if show_exp:
                _draw_text_block(
                    draw, exp_lines, font_explain, W / 2, exp_y,
                    fill="#FFFFFF", stroke_fill="#000000", stroke_width=5, line_spacing=1.3,
                )

        else:
            draw.text((W / 2, H * 0.44), profile["outro_line1"], font=font_outro, fill="#FFFFFF",
                       anchor="mm", stroke_width=5, stroke_fill="#000000")
            draw.text((W / 2, H * 0.51), profile["outro_line2"], font=font_outro, fill=accent,
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

    music_path = _find_music(profile.get("name"))
    if music_path:
        print(f"Using background music: {music_path}")
        music = AudioFileClip(music_path).with_volume_scaled(profile.get("music_volume", 0.22))
        if music.duration < total_duration:
            loops = int(total_duration / music.duration) + 1
            music = concatenate_audioclips([music] * loops)
            music = music.subclipped(0, total_duration)
        else:
            # Long real tracks (e.g. a full song) shouldn't always play the
            # same opening seconds - pick a random slice each time instead.
            max_start = music.duration - total_duration
            start = random.uniform(0, max_start)
            music = music.subclipped(start, start + total_duration)
        fade = min(1.5, total_duration / 4)
        music = music.with_effects([AudioFadeIn(fade), AudioFadeOut(fade)])
        audio = CompositeAudioClip([music, q_audio_positioned, a_audio_positioned])

    video = video.with_audio(audio)
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )
    return out_path


def _audio_files(directory):
    if not os.path.isdir(directory):
        return []
    return [
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.lower().endswith((".mp3", ".m4a", ".wav"))
    ]


def _find_music(profile_name):
    """Picks a random track from this channel's own music folder
    (assets/music/<profile_name>/), so each channel's mood stays consistent
    instead of mixing tracks across channels. Falls back to any shared
    tracks directly under assets/music/ if the channel has none of its own."""
    channel_dir = os.path.join(MUSIC_DIR, profile_name) if profile_name else None
    candidates = _audio_files(channel_dir) if channel_dir else []
    if not candidates:
        candidates = _audio_files(MUSIC_DIR)
    return random.choice(candidates) if candidates else None


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
