from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.ui.navigation import (
    clamp_frame_index,
    nearest_saved_frame_index,
    slider_to_frame_index,
    step_frame_index,
)


class NavigationTests(unittest.TestCase):
    def test_clamp_frame_index_stays_inside_dump(self) -> None:
        self.assertEqual(clamp_frame_index(-5, 100), 0)
        self.assertEqual(clamp_frame_index(50, 100), 50)
        self.assertEqual(clamp_frame_index(500, 100), 99)

    def test_step_frame_index_uses_delta_and_bounds(self) -> None:
        self.assertEqual(step_frame_index(10, 100, -10), 0)
        self.assertEqual(step_frame_index(10, 100, 10), 20)
        self.assertEqual(step_frame_index(95, 100, 10), 99)

    def test_slider_to_frame_index_accepts_tk_values(self) -> None:
        self.assertEqual(slider_to_frame_index("12.0", 100), 12)
        self.assertEqual(slider_to_frame_index("bad", 100), 0)
        self.assertEqual(slider_to_frame_index("200", 100), 99)

    def test_nearest_saved_frame_index_returns_closest_saved_frame(self) -> None:
        self.assertEqual(nearest_saved_frame_index(12, {1, 10, 25}), 10)
        self.assertEqual(nearest_saved_frame_index(18, {1, 10, 25}), 25)
        self.assertIsNone(nearest_saved_frame_index(18, set()))


if __name__ == "__main__":
    unittest.main()
