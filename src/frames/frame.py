from __future__ import annotations

from dataclasses import dataclass


PixelMatrix = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class DmdFrame:
    """A normalized DMD frame preserving exact and binary representations."""

    frame_number: int
    header: str
    exact_pixels: PixelMatrix
    binary_pixels: PixelMatrix

