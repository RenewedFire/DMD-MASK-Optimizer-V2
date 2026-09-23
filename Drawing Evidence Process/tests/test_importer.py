from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.dmd.importer import parse_dump_text


def _frame(header: str, fill: str = "0") -> str:
    row = fill * 128
    return "\n".join([header, *([row] * 32)])


class ImporterTests(unittest.TestCase):
    def test_parse_dump_text_reads_frames_without_final_blank_line(self) -> None:
        frames = parse_dump_text(_frame("0x00000001") + "\n\n" + _frame("0x00000002", "3"))

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0].header, "0x00000001")
        self.assertEqual(frames[1].pixels[0][0], 3)

    def test_parse_dump_text_rejects_bad_header(self) -> None:
        with self.assertRaises(ValueError):
            parse_dump_text("bad\n")


if __name__ == "__main__":
    unittest.main()
