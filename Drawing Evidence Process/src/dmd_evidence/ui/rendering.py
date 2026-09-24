from __future__ import annotations

import tkinter as tk

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
    scale: float,
    offset_x: float = 0,
    offset_y: float = 0,
) -> tuple[tuple[int, int, int, int, str], ...]:
    if scale <= 0:
        raise ValueError("scale must be positive")
    rectangles: list[tuple[int, int, int, int, str]] = []
    for y, row in enumerate(frame.pixels):
        for x, value in enumerate(row):
            rectangles.append(
                (
                    round(offset_x + x * scale),
                    round(offset_y + y * scale),
                    round(offset_x + (x + 1) * scale),
                    round(offset_y + (y + 1) * scale),
                    frame_pixel_color(value),
                )
            )
    return tuple(rectangles)


def frame_photo_image(frame: DmdFrame, scale: int) -> tk.PhotoImage:
    if scale <= 0:
        raise ValueError("scale must be positive")
    image = tk.PhotoImage(width=frame.width, height=frame.height)
    rows = []
    for row in frame.pixels:
        rows.append("{" + " ".join(frame_pixel_color(value) for value in row) + "}")
    image.put(" ".join(rows), to=(0, 0, frame.width, frame.height))
    if scale == 1:
        return image
    return image.zoom(scale, scale)
