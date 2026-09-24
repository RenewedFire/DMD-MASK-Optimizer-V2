from __future__ import annotations

import json
from pathlib import Path

from dmd_evidence.dmd.frame import DmdDump, DmdFrame
from dmd_evidence.dmd.hashing import hash_frame
from dmd_evidence.geometry import NativeRect
from dmd_evidence.repository import DumpRecord, EvidenceRepository, EvidenceSummaryRecord
from dmd_evidence.repository.database import deserialize_frame


class EvidenceService:
    def __init__(self, database_path: str | Path) -> None:
        self.repository = EvidenceRepository(database_path)
        self.repository.initialize()
        self.dump_record: DumpRecord | None = None
        self.last_opened_dump_was_known = False

    def close(self) -> None:
        self.repository.close()

    def open_dump(self, dump: DmdDump) -> DumpRecord:
        self.last_opened_dump_was_known = self.repository.get_dump_by_hash(
            dump.content_hash
        ) is not None
        self.dump_record = self.repository.upsert_dump(dump)
        return self.dump_record

    def submit_current_frame(
        self,
        frame: DmdFrame,
        regions: list[NativeRect] | tuple[NativeRect, ...],
        descriptor: str = "",
    ) -> None:
        if self.dump_record is None:
            raise RuntimeError("no dump is open")
        self.repository.submit_evidence(self.dump_record.id, frame, regions, descriptor)

    def saved_frame_indices(self) -> tuple[int, ...]:
        if self.dump_record is None:
            return ()
        return self.repository.evidence_frame_indices(self.dump_record.id)

    def load_regions(self, source_frame_index: int) -> list[NativeRect]:
        if self.dump_record is None:
            return []
        try:
            evidence = self.repository.get_evidence_frame(
                self.dump_record.id,
                source_frame_index,
            )
        except KeyError:
            return []
        return [
            NativeRect(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
            )
            for region in self.repository.list_regions(evidence.id)
        ]

    def counts(self) -> dict[str, int]:
        return self.repository.counts()

    def all_evidence_summaries(self) -> tuple[EvidenceSummaryRecord, ...]:
        return self.repository.list_evidence_summaries()

    def matching_evidence_summaries(
        self,
        frame: DmdFrame,
    ) -> tuple[EvidenceSummaryRecord, ...]:
        frame_hash = hash_frame(frame)
        return tuple(
            summary
            for summary in self.repository.list_evidence_summaries()
            if summary.frame_hash == frame_hash
        )

    def all_dumps(self) -> tuple[DumpRecord, ...]:
        return self.repository.list_dumps()

    def load_evidence_frame(self, evidence_frame_id: int) -> DmdFrame:
        evidence = self.repository.get_evidence_frame_by_id(evidence_frame_id)
        return deserialize_frame(evidence.frame_data)

    def load_evidence_regions(self, evidence_frame_id: int) -> list[NativeRect]:
        return [
            NativeRect(
                x=region.x,
                y=region.y,
                width=region.width,
                height=region.height,
            )
            for region in self.repository.list_regions(evidence_frame_id)
        ]

    def update_evidence_regions(
        self,
        evidence_frame_id: int,
        regions: list[NativeRect] | tuple[NativeRect, ...],
        descriptor: str | None = None,
    ) -> None:
        self.repository.update_evidence_regions(evidence_frame_id, regions, descriptor)

    def export_repository_report(self, output_path: str | Path) -> dict[str, object]:
        payload = self.repository_export_payload()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return payload

    def repository_export_payload(self) -> dict[str, object]:
        dumps = self.repository.list_dumps()
        summaries = self.repository.list_evidence_summaries()
        summaries_by_dump = {
            dump.id: tuple(summary for summary in summaries if summary.dump_id == dump.id)
            for dump in dumps
        }
        return {
            "format": "dmd-region-evidence-export",
            "format_version": 1,
            "counts": self.repository.counts(),
            "dumps": [
                {
                    "id": dump.id,
                    "content_hash": dump.content_hash,
                    "filename": dump.filename,
                    "game_name": dump.game_name,
                    "frame_count": dump.frame_count,
                    "evidence_frames": [
                        self._export_evidence_frame(summary.evidence_frame_id)
                        for summary in summaries_by_dump[dump.id]
                    ],
                }
                for dump in dumps
            ],
        }

    def _export_evidence_frame(self, evidence_frame_id: int) -> dict[str, object]:
        evidence = self.repository.get_evidence_frame_by_id(evidence_frame_id)
        frame = deserialize_frame(evidence.frame_data)
        return {
            "id": evidence.id,
            "source_frame_index": evidence.source_frame_index,
            "frame_hash": evidence.frame_hash,
            "frame_width": evidence.frame_width,
            "frame_height": evidence.frame_height,
            "descriptor": evidence.descriptor,
            "frame": {
                "source_index": frame.source_index,
                "header": frame.header,
                "width": frame.width,
                "height": frame.height,
                "pixels": frame.pixels,
            },
            "regions": [
                {
                    "x": region.x,
                    "y": region.y,
                    "width": region.width,
                    "height": region.height,
                    "display_order": region.display_order,
                }
                for region in self.repository.list_regions(evidence.id)
            ],
        }
