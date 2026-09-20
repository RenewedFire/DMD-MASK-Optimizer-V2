from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from src.frames import PixelMatrix


Point = tuple[int, int]


@dataclass(frozen=True)
class BoundingBox:
    min_x: int
    min_y: int
    max_x: int
    max_y: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1


@dataclass(frozen=True)
class LitComponent:
    component_id: int
    pixels: tuple[Point, ...]
    bounding_box: BoundingBox
    area: int
    centroid_x: float
    centroid_y: float


def find_lit_components(binary_pixels: PixelMatrix) -> tuple[LitComponent, ...]:
    height = len(binary_pixels)
    width = len(binary_pixels[0]) if height else 0
    for row in binary_pixels:
        if len(row) != width:
            raise ValueError("Binary pixel matrix must be rectangular")

    visited: set[Point] = set()
    components: list[LitComponent] = []

    for y in range(height):
        for x in range(width):
            if binary_pixels[y][x] == 0 or (x, y) in visited:
                continue
            component_pixels = _collect_component(binary_pixels, x, y, visited)
            components.append(_build_component(len(components), component_pixels))

    return tuple(components)


def components_to_payload(components: tuple[LitComponent, ...]) -> list[dict[str, object]]:
    return [
        {
            "component_id": component.component_id,
            "area": component.area,
            "bounding_box": {
                "min_x": component.bounding_box.min_x,
                "min_y": component.bounding_box.min_y,
                "max_x": component.bounding_box.max_x,
                "max_y": component.bounding_box.max_y,
                "width": component.bounding_box.width,
                "height": component.bounding_box.height,
            },
            "centroid": {
                "x": component.centroid_x,
                "y": component.centroid_y,
            },
            "pixels": [{"x": x, "y": y} for x, y in component.pixels],
        }
        for component in components
    ]


def _collect_component(
    binary_pixels: PixelMatrix,
    start_x: int,
    start_y: int,
    visited: set[Point],
) -> tuple[Point, ...]:
    height = len(binary_pixels)
    width = len(binary_pixels[0])
    queue: deque[Point] = deque([(start_x, start_y)])
    visited.add((start_x, start_y))
    pixels: list[Point] = []

    while queue:
        x, y = queue.popleft()
        pixels.append((x, y))
        for neighbor_x, neighbor_y in _neighbors_8(x, y):
            if not (0 <= neighbor_x < width and 0 <= neighbor_y < height):
                continue
            if (neighbor_x, neighbor_y) in visited:
                continue
            if binary_pixels[neighbor_y][neighbor_x] == 0:
                continue
            visited.add((neighbor_x, neighbor_y))
            queue.append((neighbor_x, neighbor_y))

    return tuple(sorted(pixels, key=lambda point: (point[1], point[0])))


def _neighbors_8(x: int, y: int) -> tuple[Point, ...]:
    return (
        (x - 1, y - 1),
        (x, y - 1),
        (x + 1, y - 1),
        (x - 1, y),
        (x + 1, y),
        (x - 1, y + 1),
        (x, y + 1),
        (x + 1, y + 1),
    )


def _build_component(component_id: int, pixels: tuple[Point, ...]) -> LitComponent:
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    area = len(pixels)
    return LitComponent(
        component_id=component_id,
        pixels=pixels,
        bounding_box=BoundingBox(
            min_x=min(xs),
            min_y=min(ys),
            max_x=max(xs),
            max_y=max(ys),
        ),
        area=area,
        centroid_x=sum(xs) / area,
        centroid_y=sum(ys) / area,
    )
