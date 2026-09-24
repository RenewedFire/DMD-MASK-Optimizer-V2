from __future__ import annotations

from dataclasses import dataclass
import unittest

import path_setup  # noqa: F401

from dmd_evidence.ui.browser import filter_evidence_summaries


@dataclass(frozen=True)
class Summary:
    dump_id: int
    filename: str
    source_frame_index: int
    region_count: int
    descriptor: str = ""


class BrowserTests(unittest.TestCase):
    def test_filter_evidence_summaries_filters_by_dump(self) -> None:
        summaries = (
            Summary(1, "a.txt", 0, 2),
            Summary(2, "b.txt", 4, 1),
        )

        filtered = filter_evidence_summaries(summaries, dump_id=2)

        self.assertEqual(filtered, (summaries[1],))

    def test_filter_evidence_summaries_filters_by_text(self) -> None:
        summaries = (
            Summary(1, "alpha.txt", 0, 2),
            Summary(2, "beta.txt", 4, 1),
        )

        filtered = filter_evidence_summaries(summaries, text="frame 5")

        self.assertEqual(filtered, (summaries[1],))

    def test_filter_evidence_summaries_combines_filters(self) -> None:
        summaries = (
            Summary(1, "alpha.txt", 0, 2),
            Summary(1, "alpha.txt", 9, 3),
            Summary(2, "beta.txt", 9, 1),
        )

        filtered = filter_evidence_summaries(summaries, dump_id=1, text="index 9")

        self.assertEqual(filtered, (summaries[1],))

    def test_filter_evidence_summaries_searches_descriptor(self) -> None:
        summaries = (
            Summary(1, "alpha.txt", 0, 2, "match sequence"),
            Summary(1, "alpha.txt", 1, 1, "other"),
        )

        filtered = filter_evidence_summaries(summaries, text="match")

        self.assertEqual(filtered, (summaries[0],))


if __name__ == "__main__":
    unittest.main()
