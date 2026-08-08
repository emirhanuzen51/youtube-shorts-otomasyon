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

# Each preset is a distinct chord/scale voicing so a channel's music matches
# its mood, without ever downloading third-party audio.
PRESETS = {
    "dogru_bilinen_yanlislar": {
        "filename": "tense_pad.wav",
        # A-minor pad: mildly moody/curious, fits a "myth about to be busted" tone.
        "freqs": [220.00, 261.63, 329.63, 440.00],
        "breathe_rate": 0.05,
        "duration": 40.0,
    },
    "dini_kissalar": {
        "filename": "reflective_pad.wav",
        # Open C-sus voicing (root/4th/5th/octave, no 3rd): warm, spacious,
        # non-dissonant - evokes a calm, reflective, spiritual mood.
        "freqs": [130.81, 174.61, 196.00, 261.63],
        "breathe_rate": 0.03,
        "duration": 40.0,
    },
}


def generate_pad(out_path, freqs, duration=40.0, breathe_rate=0.05):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave_sum = np.zeros_like(t)

    for i, freq in enumerate(freqs):
        # Slight detune + slow vibrato per voice so it feels alive, not static.
        detune = 1 + (i - 1.5) * 0.0015
        vibrato = 1 + 0.0015 * np.sin(2 * np.pi * (0.07 + i * 0.01) * t)
        voice = np.sin(2 * np.pi * freq * detune * vibrato * t)
        wave_sum += voice / len(freqs)

    # Slow "breathing" amplitude envelope so the pad swells and recedes.
    breathe = 0.6 + 0.4 * (np.sin(2 * np.pi * breathe_rate * t - np.pi / 2) * 0.5 + 0.5)
    signal = wave_sum * breathe

    # Long fade in/out so loop-splicing (done later via concatenate_audioclips) is seamless.
    fade_len = int(SAMPLE_RATE * 3)
    fade = np.linspace(0, 1, fade_len)
    signal[:fade_len] *= fade
    signal[-fade_len:] *= fade[::-1]

    # Normalize to a moderate peak; render_video.py applies its own volume_scaled on top.
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
    for profile_name, preset in PRESETS.items():
        out_path = os.path.join(MUSIC_DIR, profile_name, preset["filename"])
        path = generate_pad(out_path, preset["freqs"], preset["duration"], preset["breathe_rate"])
        print(f"Wrote {path}")
