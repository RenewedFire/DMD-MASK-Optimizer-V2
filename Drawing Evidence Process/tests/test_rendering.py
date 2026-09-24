from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.dmd.frame import DmdFrame
from dmd_evidence.ui.rendering import frame_canvas_rectangles, frame_photo_image, frame_pixel_color


class RenderingTests(unittest.TestCase):
    def test_frame_pixel_color_rejects_unknown_values(self) -> None:
        with self.assertRaises(ValueError):
            frame_pixel_color(9)

    def test_frame_canvas_rectangles_scale_native_pixels(self) -> None:
        frame = DmdFrame(
            source_index=0,
            header="0x00000001",
            width=2,
            height=1,
            pixels=((0, 3),),
        )

        rectangles = frame_canvas_rectangles(frame, scale=4)

        self.assertEqual(rectangles[0], (0, 0, 4, 4, "#000000"))
        self.assertEqual(rectangles[1], (4, 0, 8, 4, "#ffc13b"))

    def test_frame_canvas_rectangles_support_offsets(self) -> None:
        frame = DmdFrame(
            source_index=0,
            header="0x00000001",
            width=1,
            height=1,
            pixels=((3,),),
        )

        rectangles = frame_canvas_rectangles(frame, scale=4, offset_x=10, offset_y=20)

        self.assertEqual(rectangles[0], (10, 20, 14, 24, "#ffc13b"))

    def test_frame_photo_image_rejects_non_positive_scale(self) -> None:
        frame = DmdFrame(
            source_index=0,
            header="0x00000001",
            width=1,
            height=1,
            pixels=((3,),),
        )

        with self.assertRaises(ValueError):
            frame_photo_image(frame, scale=0)


if __name__ == "__main__":
    unittest.main()
