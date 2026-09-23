from __future__ import annotations

import unittest

import path_setup  # noqa: F401

from dmd_evidence.dmd.frame import DmdFrame
from dmd_evidence.dmd.hashing import hash_dump_bytes, hash_frame


class HashingTests(unittest.TestCase):
    def test_dump_hash_depends_on_content_not_filename(self) -> None:
        content = b"same dump bytes"

        self.assertEqual(hash_dump_bytes(content), hash_dump_bytes(content))

    def test_frame_hash_is_stable_for_same_pixels(self) -> None:
        frame_a = DmdFrame(
            source_index=0,
            header="0x00000001",
            width=2,
            height=2,
            pixels=((0, 1), (2, 3)),
        )
        frame_b = DmdFrame(
            source_index=7,
            header="0xffffffff",
            width=2,
            height=2,
            pixels=((0, 1), (2, 3)),
        )

        self.assertEqual(hash_frame(frame_a), hash_frame(frame_b))


if __name__ == "__main__":
    unittest.main()
