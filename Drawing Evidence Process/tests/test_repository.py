from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import path_setup  # noqa: F401

from dmd_evidence.dmd.frame import DmdDump, DmdFrame
from dmd_evidence.geometry import NativeRect
from dmd_evidence.repository import EvidenceRepository


def _test_frame(index: int = 0) -> DmdFrame:
    return DmdFrame(
        source_index=index,
        header=f"0x{index:08x}",
        width=4,
        height=2,
        pixels=((0, 1, 2, 3), (3, 2, 1, 0)),
    )


class RepositoryTests(unittest.TestCase):
    def test_submit_evidence_persists_after_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "evidence.sqlite"
            dump = DmdDump(
                filename="first.txt",
                content_hash="abc123",
                frames=(_test_frame(),),
            )

            repo = EvidenceRepository(db_path)
            repo.initialize()
            dump_record = repo.upsert_dump(dump)
            evidence = repo.submit_evidence(
                dump_record.id,
                dump.get_frame(0),
                [NativeRect(1, 0, 2, 1), NativeRect(0, 1, 4, 1)],
                descriptor="score scene",
            )
            repo.close()

            reopened = EvidenceRepository(db_path)
            reopened.initialize()
            regions = reopened.list_regions(evidence.id)

            self.assertEqual(reopened.counts()["evidence_frames"], 1)
            self.assertEqual(reopened.get_evidence_frame(dump_record.id, 0).descriptor, "score scene")
            self.assertEqual(len(regions), 2)
            self.assertEqual(regions[0].x, 1)
            reopened.close()

    def test_submit_existing_dump_frame_updates_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceRepository(Path(tmp) / "evidence.sqlite")
            repo.initialize()
            dump = DmdDump(filename="renamed.txt", content_hash="same", frames=(_test_frame(),))
            dump_record = repo.upsert_dump(dump)

            first = repo.submit_evidence(dump_record.id, dump.get_frame(0), [NativeRect(0, 0, 1, 1)])
            second = repo.submit_evidence(
                dump_record.id,
                dump.get_frame(0),
                [NativeRect(1, 0, 2, 1), NativeRect(0, 1, 4, 1)],
            )

            self.assertEqual(first.id, second.id)
            self.assertEqual(repo.counts()["evidence_frames"], 1)
            self.assertEqual(repo.counts()["regions"], 2)
            repo.close()

    def test_dump_identity_uses_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceRepository(Path(tmp) / "evidence.sqlite")
            repo.initialize()
            first = DmdDump(filename="a.txt", content_hash="same", frames=(_test_frame(),))
            second = DmdDump(filename="b.txt", content_hash="same", frames=(_test_frame(),))

            first_record = repo.upsert_dump(first)
            second_record = repo.upsert_dump(second)

            self.assertEqual(first_record.id, second_record.id)
            self.assertEqual(second_record.filename, "b.txt")
            self.assertEqual(repo.counts()["dumps"], 1)
            repo.close()

    def test_list_evidence_summaries_spans_dumps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceRepository(Path(tmp) / "evidence.sqlite")
            repo.initialize()
            first = DmdDump(filename="a.txt", content_hash="a", frames=(_test_frame(0),))
            second = DmdDump(filename="b.txt", content_hash="b", frames=(_test_frame(5),))
            first_record = repo.upsert_dump(first)
            second_record = repo.upsert_dump(second)
            repo.submit_evidence(first_record.id, first.get_frame(0), [NativeRect(0, 0, 1, 1)])
            repo.submit_evidence(
                second_record.id,
                second.get_frame(0),
                [NativeRect(0, 0, 1, 1), NativeRect(1, 0, 1, 1)],
                descriptor="bonus count",
            )

            summaries = repo.list_evidence_summaries()

            self.assertEqual(len(summaries), 2)
            self.assertEqual(summaries[0].filename, "a.txt")
            self.assertEqual(summaries[0].source_frame_index, 0)
            self.assertEqual(summaries[0].region_count, 1)
            self.assertEqual(summaries[1].filename, "b.txt")
            self.assertEqual(summaries[1].source_frame_index, 5)
            self.assertEqual(summaries[1].descriptor, "bonus count")
            self.assertEqual(summaries[1].region_count, 2)
            repo.close()

    def test_list_dumps_returns_dumps_by_filename(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceRepository(Path(tmp) / "evidence.sqlite")
            repo.initialize()
            repo.upsert_dump(DmdDump(filename="b.txt", content_hash="b", frames=(_test_frame(),)))
            repo.upsert_dump(DmdDump(filename="a.txt", content_hash="a", frames=(_test_frame(),)))

            dumps = repo.list_dumps()

            self.assertEqual([dump.filename for dump in dumps], ["a.txt", "b.txt"])
            repo.close()

    def test_update_evidence_regions_by_id_replaces_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = EvidenceRepository(Path(tmp) / "evidence.sqlite")
            repo.initialize()
            dump = DmdDump(filename="a.txt", content_hash="a", frames=(_test_frame(0),))
            dump_record = repo.upsert_dump(dump)
            evidence = repo.submit_evidence(
                dump_record.id,
                dump.get_frame(0),
                [NativeRect(0, 0, 1, 1)],
            )

            repo.update_evidence_regions(
                evidence.id,
                [NativeRect(1, 0, 2, 1), NativeRect(0, 1, 3, 1)],
                descriptor="updated descriptor",
            )
            regions = repo.list_regions(evidence.id)

            self.assertEqual(len(regions), 2)
            self.assertEqual(repo.get_evidence_frame_by_id(evidence.id).descriptor, "updated descriptor")
            self.assertEqual(regions[0].x, 1)
            self.assertEqual(regions[1].width, 3)
            repo.close()


if __name__ == "__main__":
    unittest.main()
