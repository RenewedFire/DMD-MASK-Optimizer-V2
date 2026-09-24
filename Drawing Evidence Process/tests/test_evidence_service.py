from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import path_setup  # noqa: F401

from dmd_evidence.dmd.frame import DmdDump, DmdFrame
from dmd_evidence.geometry import NativeRect
from dmd_evidence.services import EvidenceService


def _frame(index: int) -> DmdFrame:
    return DmdFrame(
        source_index=index,
        header=f"0x{index:08x}",
        width=4,
        height=2,
        pixels=((0, 1, 2, 3), (3, 2, 1, 0)),
    )


def _different_frame(index: int) -> DmdFrame:
    return DmdFrame(
        source_index=index,
        header=f"0x{index:08x}",
        width=4,
        height=2,
        pixels=((1, 1, 1, 1), (2, 2, 2, 2)),
    )


class EvidenceServiceTests(unittest.TestCase):
    def test_submit_and_load_regions_for_current_dump(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(Path(tmp) / "evidence.sqlite")
            dump = DmdDump(filename="dump.txt", content_hash="hash", frames=(_frame(0), _frame(1)))
            service.open_dump(dump)

            service.submit_current_frame(
                _frame(1),
                [NativeRect(x=1, y=0, width=2, height=1)],
                descriptor="player score",
            )

            self.assertEqual(service.saved_frame_indices(), (1,))
            self.assertEqual(service.load_regions(1), [NativeRect(x=1, y=0, width=2, height=1)])
            self.assertEqual(service.counts()["evidence_frames"], 1)
            self.assertEqual(service.counts()["regions"], 1)
            self.assertEqual(service.all_evidence_summaries()[0].descriptor, "player score")
            service.close()

    def test_load_regions_returns_empty_for_unsaved_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(Path(tmp) / "evidence.sqlite")
            dump = DmdDump(filename="dump.txt", content_hash="hash", frames=(_frame(0),))
            service.open_dump(dump)

            self.assertEqual(service.load_regions(0), [])
            service.close()

    def test_all_evidence_summaries_include_saved_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(Path(tmp) / "evidence.sqlite")
            dump = DmdDump(filename="dump.txt", content_hash="hash", frames=(_frame(0),))
            service.open_dump(dump)
            service.submit_current_frame(_frame(0), [NativeRect(x=1, y=0, width=2, height=1)])

            summaries = service.all_evidence_summaries()

            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0].filename, "dump.txt")
            self.assertEqual(summaries[0].source_frame_index, 0)
            self.assertEqual(summaries[0].region_count, 1)
            service.close()

    def test_reopen_known_dump_restores_saved_indices_and_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "evidence.sqlite"
            dump = DmdDump(filename="first-name.txt", content_hash="hash", frames=(_frame(0), _frame(1)))
            service = EvidenceService(db_path)
            service.open_dump(dump)
            self.assertFalse(service.last_opened_dump_was_known)
            service.submit_current_frame(_frame(1), [NativeRect(x=1, y=0, width=2, height=1)])
            service.close()

            renamed_dump = DmdDump(
                filename="renamed.txt",
                content_hash="hash",
                frames=(_frame(0), _frame(1)),
            )
            reopened = EvidenceService(db_path)
            reopened.open_dump(renamed_dump)

            self.assertTrue(reopened.last_opened_dump_was_known)
            self.assertEqual(reopened.saved_frame_indices(), (1,))
            self.assertEqual(
                reopened.load_regions(1),
                [NativeRect(x=1, y=0, width=2, height=1)],
            )
            reopened.close()

    def test_repository_preview_update_persists_after_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "evidence.sqlite"
            dump = DmdDump(filename="dump.txt", content_hash="hash", frames=(_frame(0),))
            service = EvidenceService(db_path)
            service.open_dump(dump)
            service.submit_current_frame(_frame(0), [NativeRect(x=1, y=0, width=1, height=1)])
            evidence_id = service.all_evidence_summaries()[0].evidence_frame_id
            service.update_evidence_regions(
                evidence_id,
                [NativeRect(x=2, y=0, width=2, height=1)],
                descriptor="preview edit",
            )
            service.close()

            reopened = EvidenceService(db_path)
            regions = reopened.load_evidence_regions(evidence_id)

            self.assertEqual(regions, [NativeRect(x=2, y=0, width=2, height=1)])
            self.assertEqual(reopened.all_evidence_summaries()[0].descriptor, "preview edit")
            reopened.close()

    def test_matching_evidence_summaries_use_exact_frame_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(Path(tmp) / "evidence.sqlite")
            repeated_frame = _frame(0)
            dump = DmdDump(
                filename="dump.txt",
                content_hash="hash",
                frames=(repeated_frame, _different_frame(1)),
            )
            service.open_dump(dump)
            service.submit_current_frame(
                repeated_frame,
                [NativeRect(x=0, y=0, width=1, height=1)],
                descriptor="known repeated frame",
            )

            duplicate_with_new_index = DmdFrame(
                source_index=9,
                header="0x99999999",
                width=repeated_frame.width,
                height=repeated_frame.height,
                pixels=repeated_frame.pixels,
            )
            matches = service.matching_evidence_summaries(duplicate_with_new_index)
            non_matches = service.matching_evidence_summaries(_different_frame(1))

            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].descriptor, "known repeated frame")
            self.assertEqual(non_matches, ())
            service.close()

    def test_export_repository_report_writes_machine_readable_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(Path(tmp) / "evidence.sqlite")
            dump = DmdDump(filename="dump.txt", content_hash="hash", frames=(_frame(0),))
            service.open_dump(dump)
            service.submit_current_frame(
                _frame(0),
                [NativeRect(x=1, y=0, width=2, height=1)],
                descriptor="score box",
            )
            export_path = Path(tmp) / "report.json"

            payload = service.export_repository_report(export_path)
            saved_payload = json.loads(export_path.read_text(encoding="utf-8"))

            self.assertEqual(payload["format"], "dmd-region-evidence-export")
            self.assertEqual(saved_payload["counts"]["dumps"], 1)
            self.assertEqual(saved_payload["counts"]["evidence_frames"], 1)
            evidence = saved_payload["dumps"][0]["evidence_frames"][0]
            self.assertEqual(evidence["descriptor"], "score box")
            self.assertEqual(evidence["source_frame_index"], 0)
            self.assertEqual(evidence["frame"]["header"], "0x00000000")
            self.assertEqual(evidence["regions"][0]["x"], 1)
            self.assertEqual(evidence["regions"][0]["width"], 2)
            service.close()


if __name__ == "__main__":
    unittest.main()
