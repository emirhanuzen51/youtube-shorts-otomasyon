#!/usr/bin/env python3
"""Create Shorts-compatible copies without changing the source videos."""
import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from shorts_video import prepare_shorts_video


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=PROJECT_ROOT / "Yeni klasör" / "Bebek",
        help="Folder containing source MP4 files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "Yeni klasör" / "Bebek_vertical",
        help="Separate folder for converted landscape videos",
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        raise FileNotFoundError(f"Source folder does not exist: {args.source_dir}")

    videos = sorted(args.source_dir.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError(f"No MP4 files found in {args.source_dir}")

    converted_count = 0
    for video_path in videos:
        result_path = prepare_shorts_video(str(video_path), str(args.output_dir))
        if os.path.abspath(result_path) != os.path.abspath(video_path):
            converted_count += 1
            print(f"Converted: {video_path.name} -> {result_path}")
        else:
            print(f"Already portrait or square: {video_path.name}")

    print(f"Finished. Converted {converted_count} of {len(videos)} source videos.")


if __name__ == "__main__":
    main()
