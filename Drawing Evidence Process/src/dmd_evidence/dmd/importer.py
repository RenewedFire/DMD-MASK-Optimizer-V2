from __future__ import annotations

from pathlib import Path
import re

from .frame import DmdDump, DmdFrame, PixelMatrix
from .hashing import hash_dump_bytes

HEADER_RE = re.compile(r"^0x[0-9a-fA-F]{8}$")
FRAME_WIDTH = 128
FRAME_HEIGHT = 32


def open_dump(path: str | Path) -> DmdDump:
    dump_path = Path(path)
    content = dump_path.read_bytes()
    text = content.decode("utf-8-sig")
    frames = parse_dump_text(text)
    return DmdDump(
        filename=dump_path.name,
        content_hash=hash_dump_bytes(content),
        frames=frames,
    )


def parse_dump_text(text: str) -> tuple[DmdFrame, ...]:
    lines = text.splitlines()
    frames: list[DmdFrame] = []
    index = 0

    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if not HEADER_RE.match(line):
            raise ValueError(f"Expected frame header at line {index + 1}, got {line!r}")

        header = line.lower()
        index += 1
        pixel_rows: list[tuple[int, ...]] = []

        while index < len(lines) and lines[index].strip():
            pixel_rows.append(_parse_pixel_row(lines[index], index + 1))
            index += 1

        if len(pixel_rows) != FRAME_HEIGHT:
            raise ValueError(
                f"Frame {len(frames)} with header {header!r} has "
                f"{len(pixel_rows)} rows; expected {FRAME_HEIGHT}"
            )

        frames.append(
            DmdFrame(
                source_index=len(frames),
                header=header,
                width=FRAME_WIDTH,
                height=FRAME_HEIGHT,
                pixels=tuple(pixel_rows),
            )
        )

    return tuple(frames)


def _parse_pixel_row(row: str, line_number: int) -> tuple[int, ...]:
    compact = "".join(row.split())
    if len(compact) != FRAME_WIDTH:
        raise ValueError(
            f"Pixel row at line {line_number} has width {len(compact)}; "
            f"expected {FRAME_WIDTH}"
        )
    if any(char not in "0123" for char in compact):
        raise ValueError(f"Pixel row at line {line_number} contains non-DMD values")
    return tuple(int(char) for char in compact)
