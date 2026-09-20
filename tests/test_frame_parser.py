from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.parsing import FrameParseError, parse_dump_file, parse_dump_text


WIDTH = 128
HEIGHT = 32
PIXELS_PER_FRAME = WIDTH * HEIGHT


def frame_text(header: str, pixels: str, terminate: bool = True) -> str:
    rows = [pixels[index : index + WIDTH] for index in range(0, len(pixels), WIDTH)]
    suffix = "\n\n" if terminate else "\n"
    return header + "\n" + "\n".join(rows) + suffix


class FrameParserTests(unittest.TestCase):
    def test_parses_dimensions_headers_frame_count_and_binary_pixels(self) -> None:
        pixels_a = ("0123" * (PIXELS_PER_FRAME // 4))
        pixels_b = ("0001" * (PIXELS_PER_FRAME // 4))
        dump = frame_text("0xabcdef12", pixels_a) + frame_text("0x0000000f", pixels_b)

        frames = parse_dump_text(dump)

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].frame_number, 0)
        self.assertEqual(frames[1].frame_number, 1)
        self.assertEqual(frames[0].header, "0xabcdef12")
        self.assertEqual(len(frames[0].exact_pixels), HEIGHT)
        self.assertTrue(all(len(row) == WIDTH for row in frames[0].exact_pixels))
        self.assertEqual(frames[0].exact_pixels[0][:8], (0, 1, 2, 3, 0, 1, 2, 3))
        self.assertEqual(frames[0].binary_pixels[0][:8], (0, 1, 1, 1, 0, 1, 1, 1))
        self.assertEqual(frames[1].exact_pixels[-1][-4:], (0, 0, 0, 1))

    def test_parse_dump_file_reads_from_path(self) -> None:
        pixels = "3" * PIXELS_PER_FRAME

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample_dump.txt"
            path.write_text(frame_text("0x1234567a", pixels), encoding="utf-8")

            frames = parse_dump_file(path)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].exact_pixels[0][0], 3)
        self.assertEqual(frames[0].binary_pixels[0][0], 1)

    def test_requires_prefixed_eight_digit_hex_header(self) -> None:
        with self.assertRaisesRegex(FrameParseError, "invalid header"):
            parse_dump_text(frame_text("NOTAHEADER", "0" * PIXELS_PER_FRAME))

    def test_rejects_bare_hex_header(self) -> None:
        with self.assertRaisesRegex(FrameParseError, "invalid header"):
            parse_dump_text(frame_text("000a58fc00", "0" * PIXELS_PER_FRAME))

    def test_accepts_real_dump_style_header(self) -> None:
        frames = parse_dump_text(frame_text("0x000a58fc", "0" * PIXELS_PER_FRAME))

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].header, "0x000a58fc")

    def test_allows_final_frame_to_end_at_eof_without_blank_line(self) -> None:
        frames = parse_dump_text(
            frame_text("0x01234567", "0" * PIXELS_PER_FRAME, terminate=False)
        )

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].header, "0x01234567")

    def test_rejects_truncated_frame(self) -> None:
        with self.assertRaisesRegex(FrameParseError, "expected 4096"):
            parse_dump_text(frame_text("0x01234567", "0" * (PIXELS_PER_FRAME - 1)))

    def test_rejects_truncated_final_frame_at_eof(self) -> None:
        with self.assertRaisesRegex(FrameParseError, "expected 4096"):
            parse_dump_text(
                frame_text("0x01234567", "0" * (PIXELS_PER_FRAME - 1), terminate=False)
            )

    def test_rejects_extra_pixel_data(self) -> None:
        with self.assertRaisesRegex(FrameParseError, "expected 4096"):
            parse_dump_text(frame_text("0x01234567", "0" * (PIXELS_PER_FRAME + 1)))

    def test_rejects_invalid_symbols(self) -> None:
        pixels = "0" * (PIXELS_PER_FRAME - 1) + "X"

        with self.assertRaisesRegex(FrameParseError, "invalid symbols"):
            parse_dump_text(frame_text("0x01234567", pixels))

    def test_rejects_invalid_pixel_states(self) -> None:
        pixels = "0" * (PIXELS_PER_FRAME - 1) + "4"

        with self.assertRaisesRegex(FrameParseError, "invalid pixel states"):
            parse_dump_text(frame_text("0x01234567", pixels))

    def test_allows_whitespace_inside_pixel_rows(self) -> None:
        row = " ".join("0123" * 32)
        dump = "0x01234567\n" + "\n".join([row] * HEIGHT) + "\n\n"

        frames = parse_dump_text(dump)

        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].exact_pixels[0][:4], (0, 1, 2, 3))

    def test_same_source_produces_same_normalized_frames(self) -> None:
        dump = frame_text("0x01234567", "1230" * (PIXELS_PER_FRAME // 4))

        first_parse = parse_dump_text(dump)
        second_parse = parse_dump_text(dump)

        self.assertEqual(first_parse, second_parse)


if __name__ == "__main__":
    unittest.main()
