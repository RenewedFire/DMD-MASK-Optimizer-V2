from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NativeRect:
    x: int
    y: int
    width: int
    height: int

    def clamped(self, frame_width: int, frame_height: int) -> "NativeRect":
        x = max(0, min(self.x, frame_width - 1))
        y = max(0, min(self.y, frame_height - 1))
        max_width = frame_width - x
        max_height = frame_height - y
        return NativeRect(
            x=x,
            y=y,
            width=max(1, min(self.width, max_width)),
            height=max(1, min(self.height, max_height)),
        )


def display_rect_to_native(
    x: float,
    y: float,
    width: float,
    height: float,
    display_width: float,
    display_height: float,
    frame_width: int,
    frame_height: int,
) -> NativeRect:
    if display_width <= 0 or display_height <= 0:
        raise ValueError("display dimensions must be positive")
    scale_x = frame_width / display_width
    scale_y = frame_height / display_height
    native = NativeRect(
        x=round(x * scale_x),
        y=round(y * scale_y),
        width=round(width * scale_x),
        height=round(height * scale_y),
    )
    return native.clamped(frame_width, frame_height)


def native_rect_to_display(
    rect: NativeRect,
    display_width: float,
    display_height: float,
    frame_width: int,
    frame_height: int,
) -> tuple[float, float, float, float]:
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be positive")
    scale_x = display_width / frame_width
    scale_y = display_height / frame_height
    return (
        rect.x * scale_x,
        rect.y * scale_y,
        rect.width * scale_x,
        rect.height * scale_y,
    )
