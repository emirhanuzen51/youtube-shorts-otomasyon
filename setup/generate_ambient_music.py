"""One-time script that procedurally generates royalty-free ambient
background pads for Shorts videos, so no external music library/licensing
is ever needed (consistent with the rest of the system's "no stock assets"
design - see render_video.py's procedural gradient background). Writes
loopable ~40s stereo WAV files into per-channel subfolders under
assets/music/<profile-name>/, which render_video.py's _find_music() picks
up automatically for that profile.

Run once (regenerates all presets below):
    python setup/generate_ambient_music.py
"""
import os
import wave

import numpy as np

MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")
SAMPLE_RATE = 44100

TRACKS = [
    {
        "channel": "dogru_bilinen_yanlislar",
        "filename": "tense_pad.wav",
        "freqs": [220.00, 261.63, 329.63, 440.00],
        "breathe_rate": 0.05,
        "duration": 40.0,
    },
    {
        "channel": "dogru_bilinen_yanlislar",
        "filename": "mystery_investigation.wav",
        "freqs": [174.61, 220.00, 277.18, 349.23],
        "breathe_rate": 0.04,
        "duration": 45.0,
    },
    {
        "channel": "dogru_bilinen_yanlislar",
        "filename": "curious_mind.wav",
        "freqs": [196.00, 246.94, 293.66, 392.00],
        "breathe_rate": 0.06,
        "duration": 45.0,
    },
    {
        "channel": "uzayin_sirlari",
        "filename": "cosmic_ambient.wav",
        "freqs": [130.81, 196.00, 261.63, 329.63, 392.00],
        "breathe_rate": 0.035,
        "duration": 45.0,
    },
    {
        "channel": "uzayin_sirlari",
        "filename": "deep_pulsar.wav",
        "freqs": [98.00, 146.83, 220.00, 293.66],
        "breathe_rate": 0.05,
        "duration": 45.0,
    },
    {
        "channel": "uzayin_sirlari",
        "filename": "stellar_nebula.wav",
        "freqs": [174.61, 261.63, 349.23, 523.25],
        "breathe_rate": 0.03,
        "duration": 45.0,
    },
    {
        "channel": "muze_sirlari",
        "filename": "ancient_relic.wav",
        "freqs": [146.83, 174.61, 220.00, 293.66, 349.23],
        "breathe_rate": 0.04,
        "duration": 45.0,
    },
    {
        "channel": "muze_sirlari",
        "filename": "lost_civilization.wav",
        "freqs": [110.00, 164.81, 220.00, 261.63],
        "breathe_rate": 0.035,
        "duration": 45.0,
    },
    {
        "channel": "muze_sirlari",
        "filename": "pharaoh_tomb.wav",
        "freqs": [130.81, 155.56, 196.00, 261.63],
        "breathe_rate": 0.045,
        "duration": 45.0,
    },
]


def generate_pad(out_path, freqs, duration=40.0, breathe_rate=0.05):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave_sum = np.zeros_like(t)

    for i, freq in enumerate(freqs):
        detune = 1 + (i - 1.5) * 0.0015
        vibrato = 1 + 0.0015 * np.sin(2 * np.pi * (0.07 + i * 0.01) * t)
        voice = np.sin(2 * np.pi * freq * detune * vibrato * t)
        wave_sum += voice / len(freqs)

    breathe = 0.6 + 0.4 * (np.sin(2 * np.pi * breathe_rate * t - np.pi / 2) * 0.5 + 0.5)
    signal = wave_sum * breathe

    fade_len = int(SAMPLE_RATE * 3)
    fade = np.linspace(0, 1, fade_len)
    signal[:fade_len] *= fade
    signal[-fade_len:] *= fade[::-1]

    signal = signal / np.max(np.abs(signal)) * 0.5
    stereo = np.stack([signal, signal], axis=1)
    pcm = (stereo * 32767).astype(np.int16)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with wave.open(out_path, "w") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(pcm.tobytes())

    return out_path


if __name__ == "__main__":
    for track in TRACKS:
        out_path = os.path.join(MUSIC_DIR, track["channel"], track["filename"])
        path = generate_pad(out_path, track["freqs"], track["duration"], track["breathe_rate"])
        print(f"Wrote {path}")
