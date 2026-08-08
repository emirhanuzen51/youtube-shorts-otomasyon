"""Free text-to-speech narration using edge-tts (no API key required)."""
import asyncio

import edge_tts

VOICE = "tr-TR-EmelNeural"


async def _synthesize(text: str, out_path: str, rate: str = "+0%", pitch: str = "+0Hz"):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate, pitch=pitch)
    await communicate.save(out_path)


def synthesize(text: str, out_path: str, rate: str = "+0%", pitch: str = "+0Hz"):
    """Render `text` to an mp3 file at `out_path`. `rate`/`pitch` let a scene
    sound more suspenseful (slower, lower) or excited (faster, higher)."""
    asyncio.run(_synthesize(text, out_path, rate, pitch))
    return out_path


if __name__ == "__main__":
    synthesize("Güneş sistemimizde en çok uyduya sahip gezegen hangisidir?", "test_tts.mp3")
    print("Wrote test_tts.mp3")
