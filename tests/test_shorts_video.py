import json
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from src.shorts_video import prepare_shorts_video, probe_video


class ShortsVideoTests(unittest.TestCase):
    def test_portrait_video_is_not_reencoded(self):
        with patch("src.shorts_video.probe_video", return_value=(1080, 1920, 30.0)):
            with patch("src.shorts_video.subprocess.run") as run:
                result = prepare_shorts_video("portrait.mp4", "converted")

        self.assertEqual(result, "portrait.mp4")
        run.assert_not_called()

    def test_landscape_video_is_converted_to_1080_by_1920(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = os.path.join(temp_dir, "landscape.mp4")
            output_dir = os.path.join(temp_dir, "converted")
            with open(source_path, "wb"):
                pass

            def fake_ffmpeg(command, **_kwargs):
                with open(command[-1], "wb"):
                    pass
                return subprocess.CompletedProcess(command, 0, "", "")

            with patch(
                "src.shorts_video.probe_video",
                side_effect=[(1920, 1080, 30.0), (1080, 1920, 30.0)],
            ):
                with patch("src.shorts_video.subprocess.run", side_effect=fake_ffmpeg) as run:
                    result = prepare_shorts_video(source_path, output_dir)

            self.assertEqual(result, os.path.join(output_dir, "landscape.mp4"))
            self.assertEqual(run.call_args.args[0][0], "ffmpeg")

    def test_video_over_shorts_duration_limit_is_rejected(self):
        metadata = {
            "streams": [{"width": 1080, "height": 1920}],
            "format": {"duration": "180.1"},
        }
        result = subprocess.CompletedProcess([], 0, json.dumps(metadata), "")
        with patch("src.shorts_video.subprocess.run", return_value=result):
            with self.assertRaisesRegex(ValueError, "must not exceed 180 seconds"):
                probe_video("too-long.mp4")


if __name__ == "__main__":
    unittest.main()
