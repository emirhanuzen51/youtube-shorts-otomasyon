"""Free text-to-speech narration using edge-tts (no API key required)."""
import asyncio

import edge_tts

DEFAULT_VOICE = "tr-TR-EmelNeural"


async def _synthesize_core(text: str, out_path: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz"):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)


async def _synthesize(text: str, out_path: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz"):
    try:
        await _synthesize_core(text, out_path, voice, rate, pitch)
    except Exception as err:
        if voice != DEFAULT_VOICE:
            print(f"[TTS WARNING] Voice '{voice}' failed ({err}). Falling back to '{DEFAULT_VOICE}'...")
            await _synthesize_core(text, out_path, DEFAULT_VOICE, rate, pitch)
        else:
            print(f"[TTS RETRY] Default voice failed ({err}), retrying once...")
            await asyncio.sleep(2)
            await _synthesize_core(text, out_path, DEFAULT_VOICE, rate, pitch)


def synthesize(text: str, out_path: str, voice: str | None = None, rate: str = "+0%", pitch: str = "+0Hz"):
    """Render `text` to an mp3 file at `out_path`. `voice` lets each channel
    profile pick its own narrator (defaults to DEFAULT_VOICE); `rate`/`pitch`
    let a scene sound more suspenseful (slower, lower) or excited (faster, higher)."""
    asyncio.run(_synthesize(text, out_path, voice or DEFAULT_VOICE, rate, pitch))
    return out_path


async def _stream_with_words(text: str, out_path: str, voice: str, rate: str, pitch: str):
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch, boundary="WordBoundary")
    words = []
    with open(out_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 10_000_000
                words.append((chunk["text"], start, start + chunk["duration"] / 10_000_000))
    return words


async def _synthesize_with_words(text: str, out_path: str, voice: str, rate: str, pitch: str):
    try:
        return await _stream_with_words(text, out_path, voice, rate, pitch)
    except Exception as err:
        if voice != DEFAULT_VOICE:
            print(f"[TTS WARNING] Voice '{voice}' failed ({err}). Falling back to '{DEFAULT_VOICE}'...")
            return await _stream_with_words(text, out_path, DEFAULT_VOICE, rate, pitch)
        else:
            print(f"[TTS RETRY] Default voice failed ({err}), retrying once...")
            await asyncio.sleep(2)
            return await _stream_with_words(text, out_path, DEFAULT_VOICE, rate, pitch)


def synthesize_with_words(text: str, out_path: str, voice: str | None = None, rate: str = "+0%", pitch: str = "+0Hz"):
    """Like `synthesize`, but also returns a list of (word, start_sec, end_sec)
    tuples timed against the generated audio - used to sync on-screen captions
    word-by-word with the narration instead of showing a static text block."""
    return asyncio.run(_synthesize_with_words(text, out_path, voice or DEFAULT_VOICE, rate, pitch))


if __name__ == "__main__":
    synthesize("Güneş sistemimizde en çok uyduya sahip gezegen hangisidir?", "test_tts.mp3")
    print("Wrote test_tts.mp3")
