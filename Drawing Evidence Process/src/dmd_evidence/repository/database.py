from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Iterable

from dmd_evidence.dmd.frame import DmdDump, DmdFrame
from dmd_evidence.dmd.hashing import hash_frame
from dmd_evidence.geometry import NativeRect

from .models import DumpRecord, EvidenceFrameRecord, EvidenceSummaryRecord, RegionRecord
from .schema import SCHEMA_SQL, SCHEMA_VERSION


class EvidenceRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def initialize(self) -> None:
        with self.connection:
            self.connection.executescript(SCHEMA_SQL)
            self._ensure_evidence_descriptor_column()
            self.connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
                (SCHEMA_VERSION,),
            )

    def _ensure_evidence_descriptor_column(self) -> None:
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(evidence_frames)").fetchall()
        }
        if "descriptor" not in columns:
            self.connection.execute(
                "ALTER TABLE evidence_frames ADD COLUMN descriptor TEXT NOT NULL DEFAULT ''"
            )

    def upsert_dump(self, dump: DmdDump, game_name: str | None = None) -> DumpRecord:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO dumps(content_hash, filename, game_name, frame_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(content_hash) DO UPDATE SET
                    filename = excluded.filename,
                    game_name = COALESCE(excluded.game_name, dumps.game_name),
                    frame_count = excluded.frame_count,
                    last_opened_at = CURRENT_TIMESTAMP
                """,
                (dump.content_hash, dump.filename, game_name, dump.frame_count),
            )
        row = self.connection.execute(
            "SELECT * FROM dumps WHERE content_hash = ?",
            (dump.content_hash,),
        ).fetchone()
        return _dump_from_row(row)

    def get_dump_by_hash(self, content_hash: str) -> DumpRecord | None:
        row = self.connection.execute(
            "SELECT * FROM dumps WHERE content_hash = ?",
            (content_hash,),
        ).fetchone()
        if row is None:
            return None
        return _dump_from_row(row)

    def list_dumps(self) -> tuple[DumpRecord, ...]:
        rows = self.connection.execute(
            "SELECT * FROM dumps ORDER BY filename"
        ).fetchall()
        return tuple(_dump_from_row(row) for row in rows)

    def submit_evidence(
        self,
        dump_id: int,
        frame: DmdFrame,
        regions: Iterable[NativeRect],
        descriptor: str = "",
    ) -> EvidenceFrameRecord:
        frame_data = _serialize_frame(frame)
        frame_digest = hash_frame(frame)
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO evidence_frames(
                    dump_id,
                    source_frame_index,
                    frame_hash,
                    frame_width,
                    frame_height,
                    frame_data,
                    descriptor
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dump_id, source_frame_index) DO UPDATE SET
                    frame_hash = excluded.frame_hash,
                    frame_width = excluded.frame_width,
                    frame_height = excluded.frame_height,
                    frame_data = excluded.frame_data,
                    descriptor = excluded.descriptor,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    dump_id,
                    frame.source_index,
                    frame_digest,
                    frame.width,
                    frame.height,
                    frame_data,
                    descriptor.strip(),
                ),
            )
            evidence_id = self.connection.execute(
                """
                SELECT id FROM evidence_frames
                WHERE dump_id = ? AND source_frame_index = ?
                """,
                (dump_id, frame.source_index),
            ).fetchone()["id"]
            self.connection.execute(
                "DELETE FROM regions WHERE evidence_frame_id = ?",
                (evidence_id,),
            )
            for order, rect in enumerate(regions):
                clamped = rect.clamped(frame.width, frame.height)
                self.connection.execute(
                    """
                    INSERT INTO regions(
                        evidence_frame_id,
                        x,
                        y,
                        width,
                        height,
                        display_order
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evidence_id,
                        clamped.x,
                        clamped.y,
                        clamped.width,
                        clamped.height,
                        order,
                    ),
                )
        return self.get_evidence_frame(dump_id, frame.source_index)

    def get_evidence_frame(self, dump_id: int, source_frame_index: int) -> EvidenceFrameRecord:
        row = self.connection.execute(
            """
            SELECT * FROM evidence_frames
            WHERE dump_id = ? AND source_frame_index = ?
            """,
            (dump_id, source_frame_index),
        ).fetchone()
        if row is None:
            raise KeyError(source_frame_index)
        return _evidence_from_row(row)

    def get_evidence_frame_by_id(self, evidence_frame_id: int) -> EvidenceFrameRecord:
        row = self.connection.execute(
            "SELECT * FROM evidence_frames WHERE id = ?",
            (evidence_frame_id,),
        ).fetchone()
        if row is None:
            raise KeyError(evidence_frame_id)
        return _evidence_from_row(row)

    def update_evidence_regions(
        self,
        evidence_frame_id: int,
        regions: Iterable[NativeRect],
        descriptor: str | None = None,
    ) -> EvidenceFrameRecord:
        evidence = self.get_evidence_frame_by_id(evidence_frame_id)
        with self.connection:
            if descriptor is None:
                self.connection.execute(
                    """
                    UPDATE evidence_frames
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (evidence_frame_id,),
                )
            else:
                self.connection.execute(
                    """
                    UPDATE evidence_frames
                    SET descriptor = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (descriptor.strip(), evidence_frame_id),
                )
            self.connection.execute(
                "DELETE FROM regions WHERE evidence_frame_id = ?",
                (evidence_frame_id,),
            )
            for order, rect in enumerate(regions):
                clamped = rect.clamped(evidence.frame_width, evidence.frame_height)
                self.connection.execute(
                    """
                    INSERT INTO regions(
                        evidence_frame_id,
                        x,
                        y,
                        width,
                        height,
                        display_order
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        evidence_frame_id,
                        clamped.x,
                        clamped.y,
                        clamped.width,
                        clamped.height,
                        order,
                    ),
                )
        return self.get_evidence_frame_by_id(evidence_frame_id)

    def list_regions(self, evidence_frame_id: int) -> tuple[RegionRecord, ...]:
        rows = self.connection.execute(
            """
            SELECT * FROM regions
            WHERE evidence_frame_id = ?
            ORDER BY display_order, id
            """,
            (evidence_frame_id,),
        ).fetchall()
        return tuple(_region_from_row(row) for row in rows)

    def evidence_frame_indices(self, dump_id: int) -> tuple[int, ...]:
        rows = self.connection.execute(
            """
            SELECT source_frame_index FROM evidence_frames
            WHERE dump_id = ?
            ORDER BY source_frame_index
            """,
            (dump_id,),
        ).fetchall()
        return tuple(row["source_frame_index"] for row in rows)

    def find_evidence_by_frame_hash(self, frame_hash: str) -> tuple[EvidenceFrameRecord, ...]:
        rows = self.connection.execute(
            """
            SELECT * FROM evidence_frames
            WHERE frame_hash = ?
            ORDER BY dump_id, source_frame_index
            """,
            (frame_hash,),
        ).fetchall()
        return tuple(_evidence_from_row(row) for row in rows)

    def list_evidence_summaries(self) -> tuple[EvidenceSummaryRecord, ...]:
        rows = self.connection.execute(
            """
            SELECT
                evidence_frames.id AS evidence_frame_id,
                evidence_frames.dump_id AS dump_id,
                dumps.filename AS filename,
                evidence_frames.source_frame_index AS source_frame_index,
                evidence_frames.frame_hash AS frame_hash,
                evidence_frames.descriptor AS descriptor,
                COUNT(regions.id) AS region_count
            FROM evidence_frames
            INNER JOIN dumps ON dumps.id = evidence_frames.dump_id
            LEFT JOIN regions ON regions.evidence_frame_id = evidence_frames.id
            GROUP BY evidence_frames.id
            ORDER BY dumps.filename, evidence_frames.source_frame_index
            """
        ).fetchall()
        return tuple(_evidence_summary_from_row(row) for row in rows)

    def counts(self) -> dict[str, int]:
        return {
            "dumps": self.connection.execute("SELECT COUNT(*) FROM dumps").fetchone()[0],
            "evidence_frames": self.connection.execute(
                "SELECT COUNT(*) FROM evidence_frames"
            ).fetchone()[0],
            "regions": self.connection.execute("SELECT COUNT(*) FROM regions").fetchone()[0],
        }


def _serialize_frame(frame: DmdFrame) -> str:
    return json.dumps(
        {
            "source_index": frame.source_index,
            "header": frame.header,
            "width": frame.width,
            "height": frame.height,
            "pixels": frame.pixels,
        },
        separators=(",", ":"),
    )


def deserialize_frame(frame_data: str) -> DmdFrame:
    payload = json.loads(frame_data)
    return DmdFrame(
        source_index=payload["source_index"],
        header=payload["header"],
        width=payload["width"],
        height=payload["height"],
        pixels=tuple(tuple(row) for row in payload["pixels"]),
    )


def _dump_from_row(row: sqlite3.Row) -> DumpRecord:
    return DumpRecord(
        id=row["id"],
        content_hash=row["content_hash"],
        filename=row["filename"],
        game_name=row["game_name"],
        frame_count=row["frame_count"],
    )


def _evidence_from_row(row: sqlite3.Row) -> EvidenceFrameRecord:
    return EvidenceFrameRecord(
        id=row["id"],
        dump_id=row["dump_id"],
        source_frame_index=row["source_frame_index"],
        frame_hash=row["frame_hash"],
        frame_width=row["frame_width"],
        frame_height=row["frame_height"],
        frame_data=row["frame_data"],
        descriptor=row["descriptor"],
    )


def _region_from_row(row: sqlite3.Row) -> RegionRecord:
    return RegionRecord(
        id=row["id"],
        evidence_frame_id=row["evidence_frame_id"],
        x=row["x"],
        y=row["y"],
        width=row["width"],
        height=row["height"],
        display_order=row["display_order"],
    )


def _evidence_summary_from_row(row: sqlite3.Row) -> EvidenceSummaryRecord:
    return EvidenceSummaryRecord(
        evidence_frame_id=row["evidence_frame_id"],
        dump_id=row["dump_id"],
        filename=row["filename"],
        source_frame_index=row["source_frame_index"],
        frame_hash=row["frame_hash"],
        descriptor=row["descriptor"],
        region_count=row["region_count"],
    )
