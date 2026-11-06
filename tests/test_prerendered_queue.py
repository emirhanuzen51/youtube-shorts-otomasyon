import unittest

from src.prerendered_queue import canonical_asset_name, select_next_asset


class PrerenderedQueueTests(unittest.TestCase):
    def test_normalizes_episode_and_transcode_aliases(self):
        self.assertEqual(canonical_asset_name("1.bölüm.mp4"), "1.bolum.mp4")
        self.assertEqual(
            canonical_asset_name("minik_kesifler-20261106-0001_horizontal.mp4"),
            "minik_kesifler-20261106-0001.mp4",
        )
        self.assertEqual(canonical_asset_name("01.mp4"), "1.mp4")

    def test_mahalle_episodes_are_ordered_and_history_aliases_are_skipped(self):
        selected = select_next_asset(
            "animai_studio",
            ["1.bölüm.mp4", "2.bölüm.mp4"],
            ["11.bolum.mp4", "3.bolum.mp4", "1.bolum.mp4"],
            [{"filename": "1.bölüm.mp4"}],
        )
        self.assertEqual(selected, ("local", "2.bölüm.mp4"))

    def test_animai_moves_to_kasa_only_after_mahalle_queue_is_finished(self):
        selected = select_next_asset(
            "animai_studio",
            [],
            ["12.mp4", "02.mp4", "1.bolum.mp4", "1.mp4"],
            [{"filename": f"{episode}.bolum.mp4"} for episode in range(1, 12)],
        )
        self.assertEqual(selected, ("remote", "1.mp4"))

    def test_minik_randomly_selects_only_new_batch_before_legacy_assets(self):
        selected = select_next_asset(
            "minik_maceralar",
            ["minik_kesifler-20261106-0001_horizontal.mp4"],
            [
                "mellofrommars-20261019-0010.mp4",
                "minik_kesifler-20261106-0001.mp4",
                "1.bolum.mp4",
            ],
            [],
            chooser=lambda choices: choices[-1],
        )
        self.assertEqual(selected, ("local", "minik_kesifler-20261106-0001_horizontal.mp4"))

    def test_minik_does_not_repeat_uploaded_aliases_or_select_other_channels(self):
        selected = select_next_asset(
            "minik_maceralar",
            [],
            [
                "minik_kesifler-20261106-0001.mp4",
                "1.bolum.mp4",
                "42.mp4",
            ],
            [{"filename": "minik_kesifler-20261106-0001_horizontal.mp4"}],
        )
        self.assertIsNone(selected)


if __name__ == "__main__":
    unittest.main()
