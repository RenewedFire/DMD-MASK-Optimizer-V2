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
            )
            repo.close()

            reopened = EvidenceRepository(db_path)
            reopened.initialize()
            regions = reopened.list_regions(evidence.id)

            self.assertEqual(reopened.counts()["evidence_frames"], 1)
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


if __name__ == "__main__":
    unittest.main()
