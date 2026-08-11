"""Renders a 1080x1920 Shorts video for a trivia question using PIL + MoviePy.

By default no stock footage is used (avoids licensing issues and external
downloads that could fail in CI): the background is a procedurally generated
animated gradient. A profile can opt into a real stock-video background via
stock_video.py (see _load_stock_background) - that path is fully optional
and always falls back to the gradient if it fails for any reason.
"""
import math
import os
import random
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, VideoFileClip, concatenate_audioclips
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

from profiles import get_profile
from stock_video import fetch_background_video
from text_sanitize import filter_to_font, tr_upper

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


def _load_stock_background(profile, question, out_path):
    """Opt-in real-video background (see stock_video.py). Returns a
    cover-cropped 1080x1920 VideoFileClip, or None if the profile doesn't
    request it, no PEXELS_API_KEY is configured, or anything about the
    fetch/decode fails - callers must treat None as "use the gradient"."""
    if not profile.get("use_stock_video"):
        return None
    query = profile.get("stock_video_query") or question.get("category", "")
    tmp_path = os.path.splitext(out_path)[0] + "_stockbg.mp4"
    fetched = fetch_background_video(query, tmp_path)
    if not fetched:
        return None
    try:
        clip = VideoFileClip(fetched)
        scale = max(W / clip.w, H / clip.h)
        clip = clip.resized(scale)
        x1, y1 = (clip.w - W) / 2, (clip.h - H) / 2
        return clip.cropped(x1=x1, y1=y1, width=W, height=H)
    except Exception as e:
        print(f"Stock video decode failed: {e}")
        return None


def _load_image_background(image_path):
    """Static-photo background (e.g. a real museum artifact image) with a
    slow "Ken Burns" zoom/pan applied per-frame in _ken_burns_frame. Loaded
    oversized once here so cropping a moving window from it is cheap."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        img = Image.open(image_path).convert("RGB")
        scale = max(W / img.width, H / img.height) * 1.15
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)
        return np.array(img)
    except Exception as e:
        print(f"Museum image load failed: {e}")
        return None


def _ken_burns_frame(bg_array, t, total_duration):
    h, w = bg_array.shape[:2]
    progress = min(t / max(total_duration, 1), 1.0)
    zoom = 1.0 + 0.10 * progress
    view_w = min(w, max(1, int(W / zoom)))
    view_h = min(h, max(1, int(H / zoom)))
    if view_w / view_h > W / H:
        view_w = int(view_h * W / H)
    else:
        view_h = int(view_w * H / W)
    x0 = int(max(0, w - view_w) * (0.25 + 0.5 * progress))
    y0 = int(max(0, h - view_h) * 0.5)
    crop = bg_array[y0:y0 + view_h, x0:x0 + view_w]
    return np.array(Image.fromarray(crop).resize((W, H), Image.LANCZOS))


def _bg_frame(t, stock_bg, image_bg, bg_top, bg_bottom, glow_top, glow_bottom, total_duration=30):
    if image_bg is not None:
        frame = _ken_burns_frame(image_bg, t, total_duration)
        # A real photo can be visually busy - dim it uniformly so text stays
        # legible even outside the readability bands drawn on top later.
        return (frame.astype(np.float32) * 0.55).astype(np.uint8)
    if stock_bg is not None:
        return stock_bg.get_frame(t % stock_bg.duration).astype(np.uint8)
    return _gradient_frame(t, bg_top, bg_bottom, glow_top, glow_bottom)


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


def _draw_karaoke_block(draw, lines, word_times, font, center_x, center_y, t_rel,
                         base_fill, highlight_fill, stroke_fill, stroke_width, line_spacing=1.15):
    """Draws a wrapped text block word-by-word in sync with narration: a word
    only appears once its spoken moment has passed, and the word being spoken
    right now is drawn in `highlight_fill`. Falls back to drawing everything
    (as if fully spoken) if `word_times` doesn't cover a given word, so a
    mismatch in word counts degrades gracefully instead of hiding text."""
    line_h, total_h = _block_metrics(draw, lines, font, stroke_width, line_spacing)
    space_w = draw.textlength(" ", font=font)
    y = center_y - total_h / 2
    word_idx = 0
    for line in lines:
        words = line.split(" ")
        widths = [draw.textlength(w, font=font) for w in words]
        line_w = sum(widths) + space_w * max(0, len(words) - 1)
        x = center_x - line_w / 2
        for w, ww in zip(words, widths):
            if word_idx < len(word_times):
                start, end = word_times[word_idx][1], word_times[word_idx][2]
            else:
                start, end = 0.0, 0.0
            if t_rel >= start:
                fill = highlight_fill if start <= t_rel < end else base_fill
                draw.text((x, y), w, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
            word_idx += 1
            x += ww + space_w
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
    pad_x, pad_y = 36, 18
    max_w = W - 40
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Long category names (some channels use full sentences) can render
    # wider than the frame at the default badge size - shrink the font
    # until the pill actually fits, instead of letting it run off both
    # edges of the video.
    size = getattr(font, "size", 46)
    while tw + pad_x * 2 > max_w and size > 22:
        size -= 4
        font = _font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
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


def build_video(question: dict, question_audio: str, answer_audio: str, out_path: str, profile: dict | None = None,
                 question_words=None, answer_words=None, explanation_words=None, bg_image_path=None):
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

    stock_bg = _load_stock_background(profile, question, out_path)
    image_bg = _load_image_background(bg_image_path)

    _measure_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    font_q, q_lines = _fit_text(question["question"], max_font=64, min_font=38, base_wrap=22, max_lines=6)
    _, q_block_h = _block_metrics(_measure_draw, q_lines, font_q, stroke_width=8)

    font_answer, a_lines = _fit_text(question["answer"], max_font=72, min_font=40, base_wrap=16, max_lines=4)
    _, a_block_h = _block_metrics(_measure_draw, a_lines, font_answer, stroke_width=8)

    font_explain, exp_lines = _fit_text(question["explanation"], max_font=42, min_font=26, base_wrap=30, max_lines=9)
    _, exp_block_h = _block_metrics(_measure_draw, exp_lines, font_explain, stroke_width=5, line_spacing=1.3)

    def make_frame(t):
        bg = _bg_frame(t, stock_bg, image_bg, bg_top, bg_bottom, glow_top, glow_bottom, total_duration)
        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img)

        if t < INTRO_DUR:
            p = _ease_out(min(t / 0.6, 1.0))
            alpha_badge_y = H * 0.42 + (1 - p) * 40
            _badge(draw, profile["video_badge"], alpha_badge_y, font_badge, fg=badge_fg, bg=badge_bg)
            if t > 0.6:
                p2 = _ease_out(min((t - 0.6) / 0.6, 1.0))
                cat_text = tr_upper(question["category"])
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
            _badge(draw, tr_upper(question["category"]), H * 0.14, font_badge, fg=badge_fg, bg=badge_bg)
            if question_words:
                _draw_karaoke_block(
                    draw, q_lines, question_words, font_q, W / 2, block_top + q_block_h / 2, t - question_start,
                    base_fill="#FFFFFF", highlight_fill=accent, stroke_fill="#000000", stroke_width=8,
                )
            else:
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
            _badge(draw, tr_upper(question["category"]), H * 0.14, font_badge, fg=badge_fg, bg=badge_bg)
            if question_words:
                _draw_karaoke_block(
                    draw, q_lines, question_words, font_q, W / 2, block_top + q_block_h / 2, t - question_start,
                    base_fill="#FFFFFF", highlight_fill=accent, stroke_fill="#000000", stroke_width=8,
                )
            else:
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
            bg2 = _bg_frame(t, stock_bg, image_bg, bg_top, bg_bottom, glow_top, glow_bottom, total_duration)
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
            a_t_rel = t - reveal_start
            if answer_words:
                _draw_karaoke_block(
                    draw, a_lines, answer_words, font_answer, W / 2, answer_top + a_block_h / 2, a_t_rel,
                    base_fill=accent, highlight_fill="#FFFFFF", stroke_fill="#000000", stroke_width=8,
                )
            else:
                _draw_text_block(
                    draw, a_lines, font_answer, W / 2, answer_top + a_block_h / 2,
                    fill=accent, stroke_fill="#000000", stroke_width=8,
                )
            if show_exp:
                if explanation_words:
                    _draw_karaoke_block(
                        draw, exp_lines, explanation_words, font_explain, W / 2, exp_y, a_t_rel,
                        base_fill="#FFFFFF", highlight_fill=accent, stroke_fill="#000000", stroke_width=5,
                        line_spacing=1.3,
                    )
                else:
                    _draw_text_block(
                        draw, exp_lines, font_explain, W / 2, exp_y,
                        fill="#FFFFFF", stroke_fill="#000000", stroke_width=5, line_spacing=1.3,
                    )

        else:
            draw.text((W / 2, H * 0.44), profile["outro_line1"], font=font_outro, fill="#FFFFFF",
                       anchor="mm", stroke_width=5, stroke_fill="#000000")
            draw.text((W / 2, H * 0.51), profile["outro_line2"], font=font_outro, fill=accent,
                       anchor="mm", stroke_width=5, stroke_fill="#000000")
            # Pulsing subscribe/like call-to-action badge for the outro.
            pulse = 1.0 + 0.08 * math.sin((t - outro_start) * 5)
            sub_font = _font(max(32, int(44 * pulse)))
            _badge(draw, profile.get("subscribe_cta", "ABONE OL & BEĞEN"), H * 0.62, sub_font,
                   fg=badge_fg, bg=badge_bg)

        return np.array(img)

    # Grab a frame from the question scene (not the answer reveal!) to use as
    # the YouTube thumbnail, so the auto-selected preview doesn't spoil the answer.
    # Must be late in the scene (just before the countdown starts), not early:
    # the karaoke captions reveal words progressively as they're spoken, so an
    # early frame would catch the question text mostly still hidden/blank.
    thumb_time = max(question_start + 0.1, countdown_start - 0.3)
    thumb_path = os.path.splitext(out_path)[0] + "_thumb.jpg"
    Image.fromarray(make_frame(thumb_time)).convert("RGB").save(thumb_path, quality=90)

    video = VideoClip(make_frame, duration=total_duration).with_fps(FPS)

    q_audio_positioned = q_clip.with_start(question_start)
    a_audio_positioned = a_clip.with_start(reveal_start)
    audio = CompositeAudioClip([q_audio_positioned, a_audio_positioned])

    music_path = _find_music(profile)
    if music_path:
        print(f"Using background music: {music_path}")
        music = AudioFileClip(music_path)
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
        # Real, user-supplied tracks can be mastered far quieter (or louder)
        # than our own procedurally-generated pads - normalize to a common
        # peak level first so the profile's music_volume means the same
        # thing regardless of source file loudness.
        music = _peak_normalize(music)
        music = music.with_volume_scaled(profile.get("music_volume", 0.22))
        fade = min(1.5, total_duration / 4)
        music = music.with_effects([AudioFadeIn(fade), AudioFadeOut(fade)])
        audio = CompositeAudioClip([music, q_audio_positioned, a_audio_positioned])

    video = video.with_audio(audio)
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        preset="medium", threads=4, logger=None,
    )
    return out_path


def _peak_normalize(clip, target_peak=0.5, max_gain=12.0):
    """Scales an audio clip so its peak amplitude matches `target_peak`,
    so a quiet source file (e.g. a low-mastered mp3) is boosted to the same
    reference loudness our procedurally-generated pads are normalized to."""
    arr = clip.to_soundarray(fps=22050)
    peak = float(np.max(np.abs(arr))) if arr.size else 0.0
    if peak < 1e-4:
        return clip
    factor = min(target_peak / peak, max_gain)
    return clip.with_volume_scaled(factor)


def _audio_files(directory):
    if not os.path.isdir(directory):
        return []
    return [
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.lower().endswith((".mp3", ".m4a", ".wav"))
    ]


def _find_music(profile):
    """Picks this channel's music. If the profile pins an exact track via
    "music_file" (filename inside assets/music/<profile_name>/), that file
    is always used. Otherwise a random track from the channel's own folder
    is picked, so each channel's mood stays consistent instead of mixing
    tracks across channels. Falls back to shared tracks directly under
    assets/music/ if the channel has none of its own."""
    profile_name = profile.get("name")
    channel_dir = os.path.join(MUSIC_DIR, profile_name) if profile_name else None

    pinned = profile.get("music_file")
    if pinned and channel_dir:
        pinned_path = os.path.join(channel_dir, pinned)
        if os.path.isfile(pinned_path):
            return pinned_path

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
