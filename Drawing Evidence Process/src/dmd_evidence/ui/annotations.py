from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dmd_evidence.geometry import NativeRect


class HitKind(str, Enum):
    BODY = "body"
    NW = "nw"
    NE = "ne"
    SW = "sw"
    SE = "se"


@dataclass(frozen=True)
class AnnotationHit:
    index: int
    kind: HitKind


def normalized_rect(x1: int, y1: int, x2: int, y2: int) -> NativeRect:
    min_x = min(x1, x2)
    min_y = min(y1, y2)
    max_x = max(x1, x2)
    max_y = max(y1, y2)
    return NativeRect(
        x=min_x,
        y=min_y,
        width=max(1, max_x - min_x + 1),
        height=max(1, max_y - min_y + 1),
    )


def move_rect(rect: NativeRect, dx: int, dy: int, frame_width: int, frame_height: int) -> NativeRect:
    return NativeRect(
        x=rect.x + dx,
        y=rect.y + dy,
        width=rect.width,
        height=rect.height,
    ).clamped(frame_width, frame_height)


def resize_rect(
    rect: NativeRect,
    handle: HitKind,
    native_x: int,
    native_y: int,
    frame_width: int,
    frame_height: int,
) -> NativeRect:
    x1 = rect.x
    y1 = rect.y
    x2 = rect.x + rect.width - 1
    y2 = rect.y + rect.height - 1
    if handle == HitKind.NW:
        x1, y1 = native_x, native_y
    elif handle == HitKind.NE:
        x2, y1 = native_x, native_y
    elif handle == HitKind.SW:
        x1, y2 = native_x, native_y
    elif handle == HitKind.SE:
        x2, y2 = native_x, native_y
    else:
        return rect
    return normalized_rect(x1, y1, x2, y2).clamped(frame_width, frame_height)


def hit_test(
    rects: tuple[NativeRect, ...] | list[NativeRect],
    native_x: int,
    native_y: int,
    handle_radius: int = 1,
) -> AnnotationHit | None:
    for index in range(len(rects) - 1, -1, -1):
        rect = rects[index]
        x1 = rect.x
        y1 = rect.y
        x2 = rect.x + rect.width - 1
        y2 = rect.y + rect.height - 1
        handles = (
            (HitKind.NW, x1, y1),
            (HitKind.NE, x2, y1),
            (HitKind.SW, x1, y2),
            (HitKind.SE, x2, y2),
        )
        for kind, handle_x, handle_y in handles:
            if abs(native_x - handle_x) <= handle_radius and abs(native_y - handle_y) <= handle_radius:
                return AnnotationHit(index=index, kind=kind)
        if x1 <= native_x <= x2 and y1 <= native_y <= y2:
            return AnnotationHit(index=index, kind=HitKind.BODY)
    return None
