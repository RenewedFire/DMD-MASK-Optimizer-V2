from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.geometry import NativeRect, display_rect_to_native, native_rect_to_display


class CoordinateTests(unittest.TestCase):
    def test_display_rect_maps_to_native_coordinates(self) -> None:
        rect = display_rect_to_native(
            x=80,
            y=40,
            width=160,
            height=80,
            display_width=1024,
            display_height=256,
            frame_width=128,
            frame_height=32,
        )

        self.assertEqual(rect, NativeRect(x=10, y=5, width=20, height=10))

    def test_native_rect_maps_to_display_coordinates(self) -> None:
        display = native_rect_to_display(
            NativeRect(x=10, y=5, width=20, height=10),
            display_width=1024,
            display_height=256,
            frame_width=128,
            frame_height=32,
        )

        self.assertEqual(display, (80, 40, 160, 80))

    def test_rect_clamps_to_frame_bounds(self) -> None:
        rect = NativeRect(x=126, y=31, width=10, height=10).clamped(128, 32)

        self.assertEqual(rect, NativeRect(x=126, y=31, width=2, height=1))


if __name__ == "__main__":
    unittest.main()
