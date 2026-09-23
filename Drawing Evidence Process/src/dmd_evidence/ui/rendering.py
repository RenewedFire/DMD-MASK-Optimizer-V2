from __future__ import annotations

from dmd_evidence.dmd.frame import DmdFrame

DMD_PALETTE = {
    0: "#000000",
    1: "#6b260b",
    2: "#c7650d",
    3: "#ffc13b",
}


def frame_pixel_color(value: int) -> str:
    try:
        return DMD_PALETTE[value]
    except KeyError as exc:
        raise ValueError(f"unsupported DMD pixel value: {value}") from exc


def frame_canvas_rectangles(
    frame: DmdFrame,
    scale: int,
) -> tuple[tuple[int, int, int, int, str], ...]:
    if scale <= 0:
        raise ValueError("scale must be positive")
    rectangles: list[tuple[int, int, int, int, str]] = []
    for y, row in enumerate(frame.pixels):
        for x, value in enumerate(row):
            rectangles.append(
                (
                    x * scale,
                    y * scale,
                    (x + 1) * scale,
                    (y + 1) * scale,
                    frame_pixel_color(value),
                )
            )
    return tuple(rectangles)
