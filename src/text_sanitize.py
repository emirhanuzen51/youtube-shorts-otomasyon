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
    "‘": "'", "’": "'", "‚": "'",
    "“": '"', "”": '"', "„": '"',
    "–": "-", "—": "-", "−": "-",
    "…": "...", " ": " ",
    "•": "-", "‹": "<", "›": ">",
}

_MARKDOWN_CHARS = re.compile(r"[*_`#~^]")
_WHITESPACE = re.compile(r"\s+")
_TR_UPPER_MAP = str.maketrans({"i": "İ", "ı": "I"})


def tr_upper(text: str) -> str:
    """Turkish-correct uppercasing. Python's plain str.upper() uses
    Germanic casing rules where both 'i' and 'ı' collapse to dotless 'I'
    (so "bilim" -> "BILIM" instead of the correct "BİLİM"). Swapping the
    Turkish i/ı first, then upper-casing the rest, fixes that."""
    if not text:
        return text
    return text.translate(_TR_UPPER_MAP).upper()


def normalize_text(text: str) -> str:
    """Font-agnostic cleanup: typographic punctuation -> plain ASCII, strip markdown."""
    if not text:
        return text
    # Gemini's JSON output can occasionally return Turkish letters (ı, ğ, ş,
    # ö, ü, ç) as a base letter + combining diacritic instead of the normal
    # single precomposed character. That decomposed form isn't in the video
    # font's charset (so filter_to_font silently mangles it) and isn't
    # recognized as a real word by edge-tts (so it gets spelled out letter
    # by letter instead of pronounced). Canonicalizing to NFC here, right
    # after the Gemini response is parsed, keeps both the on-screen text and
    # the narration audio consistent and normal.
    text = unicodedata.normalize("NFC", text)
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
