from __future__ import annotations

import hashlib

from .frame import DmdFrame


def hash_dump_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def canonical_frame_bytes(frame: DmdFrame) -> bytes:
    rows = ["".join(str(pixel) for pixel in row) for row in frame.pixels]
    payload = f"{frame.width}x{frame.height}\n" + "\n".join(rows)
    return payload.encode("ascii")


def hash_frame(frame: DmdFrame) -> str:
    return hashlib.sha256(canonical_frame_bytes(frame)).hexdigest()
