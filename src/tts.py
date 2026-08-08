"""Free text-to-speech narration using edge-tts (no API key required)."""
import asyncio

import edge_tts

VOICE = "tr-TR-EmelNeural"


async def _synthesize(text: str, out_path: str, rate: str = "+0%"):
    communicate = edge_tts.Communicate(text, voice=VOICE, rate=rate)
    await communicate.save(out_path)


def synthesize(text: str, out_path: str, rate: str = "+0%"):
    """Render `text` to an mp3 file at `out_path`."""
    asyncio.run(_synthesize(text, out_path, rate))
    return out_path


if __name__ == "__main__":
    synthesize("Güneş sistemimizde en çok uyduya sahip gezegen hangisidir?", "test_tts.mp3")
    print("Wrote test_tts.mp3")
