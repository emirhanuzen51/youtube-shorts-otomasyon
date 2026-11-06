"""Probe and convert videos to a Shorts-compatible portrait format."""
import json
import os
import subprocess


MAX_SHORTS_DURATION_SECONDS = 180


def probe_video(path: str) -> tuple[int, int, float]:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height:format=duration",
            "-of",
            "json",
            path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not inspect video {os.path.basename(path)}: {result.stderr.strip()}")

    try:
        metadata = json.loads(result.stdout)
        stream = metadata["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
        duration = float(metadata["format"]["duration"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Invalid video metadata for {os.path.basename(path)}") from error

    if width <= 0 or height <= 0:
        raise RuntimeError(f"Invalid video dimensions for {os.path.basename(path)}: {width}x{height}")
    if duration > MAX_SHORTS_DURATION_SECONDS:
        raise ValueError(
            f"{os.path.basename(path)} is {duration:.1f}s long; Shorts videos must not exceed "
            f"{MAX_SHORTS_DURATION_SECONDS} seconds"
        )
    return width, height, duration


def prepare_shorts_video(source_path: str, output_dir: str) -> str:
    width, height, _ = probe_video(source_path)
    if width <= height:
        return source_path

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, os.path.basename(source_path))
    if os.path.exists(output_path) and os.path.getmtime(output_path) >= os.path.getmtime(source_path):
        output_width, output_height, _ = probe_video(output_path)
        if output_width == 1080 and output_height == 1920:
            return output_path

    result = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            source_path,
            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-map",
            "0:v:0",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            "-y",
            output_path,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"Could not convert {os.path.basename(source_path)}: {result.stderr.strip()}")

    output_width, output_height, _ = probe_video(output_path)
    if (output_width, output_height) != (1080, 1920):
        raise RuntimeError(
            f"Converted video has unexpected dimensions: {output_width}x{output_height}"
        )
    return output_path
