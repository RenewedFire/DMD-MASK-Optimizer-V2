from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.geometry import NativeRect
from dmd_evidence.ui.annotations import HitKind, hit_test, move_rect, normalized_rect, resize_rect


class AnnotationTests(unittest.TestCase):
    def test_normalized_rect_accepts_reverse_drag(self) -> None:
        rect = normalized_rect(10, 8, 4, 2)

        self.assertEqual(rect, NativeRect(x=4, y=2, width=7, height=7))

    def test_hit_test_prefers_topmost_rect(self) -> None:
        hit = hit_test(
            [
                NativeRect(x=0, y=0, width=20, height=10),
                NativeRect(x=5, y=5, width=20, height=10),
            ],
            native_x=10,
            native_y=8,
        )

        self.assertIsNotNone(hit)
        self.assertEqual(hit.index, 1)
        self.assertEqual(hit.kind, HitKind.BODY)

    def test_hit_test_detects_resize_handle(self) -> None:
        hit = hit_test([NativeRect(x=10, y=5, width=6, height=4)], native_x=15, native_y=8)

        self.assertIsNotNone(hit)
        self.assertEqual(hit.kind, HitKind.SE)

    def test_move_rect_clamps_to_frame(self) -> None:
        rect = move_rect(NativeRect(x=120, y=28, width=10, height=8), 10, 10, 128, 32)

        self.assertEqual(rect, NativeRect(x=127, y=31, width=1, height=1))

    def test_resize_rect_uses_selected_handle(self) -> None:
        rect = resize_rect(
            NativeRect(x=10, y=5, width=8, height=6),
            HitKind.NW,
            native_x=8,
            native_y=3,
            frame_width=128,
            frame_height=32,
        )

        self.assertEqual(rect, NativeRect(x=8, y=3, width=10, height=8))


if __name__ == "__main__":
    unittest.main()
