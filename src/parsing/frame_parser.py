from __future__ import annotations

import re
from pathlib import Path

from src.config import get_config
from src.frames.frame import DmdFrame, PixelMatrix


HEADER_PATTERN = re.compile(r"^0x[0-9a-fA-F]{8}$")


class FrameParseError(ValueError):
    """Raised when a raw DMD dump cannot be normalized into frames."""


def parse_dump_file(path: Path | str) -> list[DmdFrame]:
    return parse_dump_text(Path(path).read_text(encoding="utf-8"))


def parse_dump_text(text: str) -> list[DmdFrame]:
    config = get_config()
    lines = text.splitlines()
    frames: list[DmdFrame] = []
    index = 0

    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1

        if index >= len(lines):
            break

        header = lines[index].strip()
        if not HEADER_PATTERN.fullmatch(header):
            raise FrameParseError(
                f"Frame {len(frames)} has invalid header at line {index + 1}: {header!r}"
            )
        index += 1

        pixel_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            pixel_lines.append(lines[index].strip())
            index += 1

        exact_pixels = _parse_pixel_lines(
            pixel_lines=pixel_lines,
            frame_number=len(frames),
            header=header,
            width=config.dmd_width,
            height=config.dmd_height,
            valid_states=config.valid_pixel_states,
        )
        frames.append(
            DmdFrame(
                frame_number=len(frames),
                header=header,
                exact_pixels=exact_pixels,
                binary_pixels=_to_binary_pixels(exact_pixels),
            )
        )

    return frames


def _parse_pixel_lines(
    *,
    pixel_lines: list[str],
    frame_number: int,
    header: str,
    width: int,
    height: int,
    valid_states: tuple[int, ...],
) -> PixelMatrix:
    if not pixel_lines:
        raise FrameParseError(f"Frame {frame_number} with header {header!r} has no pixel data")

    expected_pixels = width * height
    symbols = "".join("".join(line.split()) for line in pixel_lines)

    invalid_symbols = sorted({symbol for symbol in symbols if not symbol.isdigit()})
    if invalid_symbols:
        raise FrameParseError(
            f"Frame {frame_number} with header {header!r} contains invalid symbols: "
            f"{''.join(invalid_symbols)!r}"
        )

    pixels = [int(symbol) for symbol in symbols]
    invalid_states = sorted({pixel for pixel in pixels if pixel not in valid_states})
    if invalid_states:
        raise FrameParseError(
            f"Frame {frame_number} with header {header!r} contains invalid pixel states: "
            f"{invalid_states}"
        )

    if len(pixels) != expected_pixels:
        raise FrameParseError(
            f"Frame {frame_number} with header {header!r} has {len(pixels)} pixels; "
            f"expected {expected_pixels}"
        )

    rows = [
        tuple(pixels[row_start : row_start + width])
        for row_start in range(0, expected_pixels, width)
    ]
    return tuple(rows)


def _to_binary_pixels(exact_pixels: PixelMatrix) -> PixelMatrix:
    return tuple(tuple(1 if pixel else 0 for pixel in row) for row in exact_pixels)
