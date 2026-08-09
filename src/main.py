"""Orchestrates the full daily pipeline: generate -> narrate -> render -> upload.

Which channel/exam this runs for is picked via the CONTENT_PROFILE env var
(see profiles.py), so the same code drives every exam-prep channel.
"""
import argparse
import os

from generate_question import generate_question
from profiles import get_profile
from render_video import build_video
from tts import synthesize_with_words
from upload_youtube import upload_video

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


def _strip_prefix_words(words, prefix):
    """Drops the leading words belonging to a spoken-but-not-displayed intro
    prefix (e.g. question_intro/answer_intro), keeping the remaining words'
    original clip-relative timestamps untouched."""
    n = len(prefix.split()) if prefix else 0
    return words[n:]


def run(upload: bool = True):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    profile = get_profile()
    print(f"Profile: {profile['name']}")

    print("Generating question...")
    question = generate_question(profile)
    print(f"  {question['category']}: {question['question']} -> {question['answer']}")

    q_audio = os.path.join(OUTPUT_DIR, "question.mp3")
    a_audio = os.path.join(OUTPUT_DIR, "answer.mp3")
    print("Synthesizing narration...")
    voice = profile.get("voice")
    question_intro = profile.get("question_intro", "")
    question_narration = f"{question_intro} {question['question']}".strip()
    q_words = synthesize_with_words(
        question_narration, q_audio, voice=voice,
        rate=profile.get("question_rate", "+0%"), pitch=profile.get("question_pitch", "+0Hz"),
    )
    question_words = _strip_prefix_words(q_words, question_intro)

    answer_intro = profile.get("answer_intro", "Cevap:")
    a_words = synthesize_with_words(
        f"{answer_intro} {question['answer']}. {question['explanation']}", a_audio, voice=voice,
        rate=profile.get("answer_rate", "+0%"), pitch=profile.get("answer_pitch", "+0Hz"),
    )
    answer_words = _strip_prefix_words(a_words, answer_intro)
    answer_n = len(question["answer"].split())
    answer_words, explanation_words = answer_words[:answer_n], answer_words[answer_n:]

    video_path = os.path.join(OUTPUT_DIR, "short.mp4")
    thumb_path = os.path.join(OUTPUT_DIR, "short_thumb.jpg")
    print("Rendering video...")
    build_video(
        question, q_audio, a_audio, video_path, profile,
        question_words=question_words, answer_words=answer_words, explanation_words=explanation_words,
    )
    print(f"  wrote {video_path}")

    if upload:
        print("Uploading to YouTube...")
        upload_video(video_path, question, thumbnail_path=thumb_path, profile=profile)
    else:
        print("Skipping upload (--no-upload).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-upload", action="store_true", help="Render locally without uploading to YouTube")
    args = parser.parse_args()
    run(upload=not args.no_upload)
