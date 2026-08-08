"""Orchestrates the full daily pipeline: generate -> narrate -> render -> upload.

Which channel/exam this runs for is picked via the CONTENT_PROFILE env var
(see profiles.py), so the same code drives every exam-prep channel.
"""
import argparse
import os

from generate_question import generate_question
from profiles import get_profile
from render_video import build_video
from tts import synthesize
from upload_youtube import upload_video

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")


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
    synthesize(question["question"], q_audio)
    answer_intro = profile.get("answer_intro", "Cevap:")
    synthesize(f"{answer_intro} {question['answer']}. {question['explanation']}", a_audio)

    video_path = os.path.join(OUTPUT_DIR, "short.mp4")
    thumb_path = os.path.join(OUTPUT_DIR, "short_thumb.jpg")
    print("Rendering video...")
    build_video(question, q_audio, a_audio, video_path, profile)
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
