from __future__ import annotations

from dataclasses import dataclass


PixelMatrix = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class DmdFrame:
    source_index: int
    header: str
    width: int
    height: int
    pixels: PixelMatrix


@dataclass(frozen=True)
class DmdDump:
    filename: str
    content_hash: str
    frames: tuple[DmdFrame, ...]

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def width(self) -> int:
        return self.frames[0].width if self.frames else 0

    @property
    def height(self) -> int:
        return self.frames[0].height if self.frames else 0

    def get_frame(self, index: int) -> DmdFrame:
        return self.frames[index]
