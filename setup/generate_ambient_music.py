"""One-time script that procedurally generates a royalty-free ambient
background pad for Shorts videos, so no external music library/licensing
is ever needed (consistent with the rest of the system's "no stock assets"
design). Writes a loopable ~40s stereo WAV to assets/music/.

Run once:
    python setup/generate_ambient_music.py
"""
import os
import wave

import numpy as np

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "music", "ambient_pad.wav")

SAMPLE_RATE = 44100
DURATION = 40.0
# A soft A-minor pad (A3, C4, E4) plus a quiet octave shimmer.
FREQS = [220.00, 261.63, 329.63, 440.00]


def generate():
    t = np.linspace(0, DURATION, int(SAMPLE_RATE * DURATION), endpoint=False)
    wave_sum = np.zeros_like(t)

    for i, freq in enumerate(FREQS):
        # Slight detune + slow vibrato per voice so it feels alive, not static.
        detune = 1 + (i - 1.5) * 0.0015
        vibrato = 1 + 0.0015 * np.sin(2 * np.pi * (0.07 + i * 0.01) * t)
        voice = np.sin(2 * np.pi * freq * detune * vibrato * t)
        wave_sum += voice / len(FREQS)

    # Slow "breathing" amplitude envelope so the pad swells and recedes.
    breathe = 0.6 + 0.4 * (np.sin(2 * np.pi * 0.05 * t - np.pi / 2) * 0.5 + 0.5)
    signal = wave_sum * breathe

    # Long fade in/out so loop-splicing (done later via concatenate_audioclips) is seamless.
    fade_len = int(SAMPLE_RATE * 3)
    fade = np.linspace(0, 1, fade_len)
    signal[:fade_len] *= fade
    signal[-fade_len:] *= fade[::-1]

    # Normalize to a moderate peak; render_video.py applies its own volume_scaled(0.12) on top.
    signal = signal / np.max(np.abs(signal)) * 0.5
    stereo = np.stack([signal, signal], axis=1)
    pcm = (stereo * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with wave.open(OUT_PATH, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())

    return OUT_PATH


if __name__ == "__main__":
    path = generate()
    print(f"Wrote {path}")
