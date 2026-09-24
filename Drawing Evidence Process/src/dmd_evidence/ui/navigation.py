from __future__ import annotations


def clamp_frame_index(index: int, frame_count: int) -> int:
    if frame_count <= 0:
        return 0
    return max(0, min(index, frame_count - 1))


def step_frame_index(index: int, frame_count: int, delta: int) -> int:
    return clamp_frame_index(index + delta, frame_count)


def slider_to_frame_index(value: str | float | int, frame_count: int) -> int:
    try:
        index = round(float(value))
    except (TypeError, ValueError):
        index = 0
    return clamp_frame_index(index, frame_count)


def nearest_saved_frame_index(
    approximate_index: int,
    saved_indices: set[int] | tuple[int, ...] | list[int],
) -> int | None:
    if not saved_indices:
        return None
    return min(saved_indices, key=lambda index: (abs(index - approximate_index), index))
