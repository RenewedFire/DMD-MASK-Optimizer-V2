from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DumpRecord:
    id: int
    content_hash: str
    filename: str
    game_name: str | None
    frame_count: int


@dataclass(frozen=True)
class EvidenceFrameRecord:
    id: int
    dump_id: int
    source_frame_index: int
    frame_hash: str
    frame_width: int
    frame_height: int
    frame_data: str
    descriptor: str


@dataclass(frozen=True)
class RegionRecord:
    id: int
    evidence_frame_id: int
    x: int
    y: int
    width: int
    height: int
    display_order: int


@dataclass(frozen=True)
class EvidenceSummaryRecord:
    evidence_frame_id: int
    dump_id: int
    filename: str
    source_frame_index: int
    frame_hash: str
    descriptor: str
    region_count: int
