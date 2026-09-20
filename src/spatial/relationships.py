from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from src.spatial.components import BoundingBox, LitComponent


@dataclass(frozen=True)
class ComponentRelationship:
    component_a_id: int
    component_b_id: int
    horizontal_gap: int
    vertical_gap: int
    edge_distance: float
    centroid_distance: float
    x_overlap: int
    y_overlap: int
    x_overlap_ratio: float
    y_overlap_ratio: float
    area_ratio: float
    width_ratio: float
    height_ratio: float
    top_delta: int
    bottom_delta: int
    left_delta: int
    right_delta: int
    touches: bool
    contains: bool
    horizontal_adjacent: bool
    vertical_adjacent: bool


def find_component_relationships(
    components: tuple[LitComponent, ...],
) -> tuple[ComponentRelationship, ...]:
    relationships: list[ComponentRelationship] = []
    for index, component_a in enumerate(components):
        for component_b in components[index + 1 :]:
            relationships.append(component_relationship(component_a, component_b))
    return tuple(relationships)


def relationships_to_payload(
    relationships: tuple[ComponentRelationship, ...],
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    selected = relationships if limit is None else relationships[:limit]
    return [
        {
            "component_a_id": relationship.component_a_id,
            "component_b_id": relationship.component_b_id,
            "horizontal_gap": relationship.horizontal_gap,
            "vertical_gap": relationship.vertical_gap,
            "edge_distance": relationship.edge_distance,
            "centroid_distance": relationship.centroid_distance,
            "x_overlap": relationship.x_overlap,
            "y_overlap": relationship.y_overlap,
            "x_overlap_ratio": relationship.x_overlap_ratio,
            "y_overlap_ratio": relationship.y_overlap_ratio,
            "area_ratio": relationship.area_ratio,
            "width_ratio": relationship.width_ratio,
            "height_ratio": relationship.height_ratio,
            "top_delta": relationship.top_delta,
            "bottom_delta": relationship.bottom_delta,
            "left_delta": relationship.left_delta,
            "right_delta": relationship.right_delta,
            "touches": relationship.touches,
            "contains": relationship.contains,
            "horizontal_adjacent": relationship.horizontal_adjacent,
            "vertical_adjacent": relationship.vertical_adjacent,
        }
        for relationship in selected
    ]


def component_relationship(
    component_a: LitComponent,
    component_b: LitComponent,
) -> ComponentRelationship:
    box_a = component_a.bounding_box
    box_b = component_b.bounding_box
    horizontal_gap = _axis_gap(box_a.min_x, box_a.max_x, box_b.min_x, box_b.max_x)
    vertical_gap = _axis_gap(box_a.min_y, box_a.max_y, box_b.min_y, box_b.max_y)
    x_overlap = _axis_overlap(box_a.min_x, box_a.max_x, box_b.min_x, box_b.max_x)
    y_overlap = _axis_overlap(box_a.min_y, box_a.max_y, box_b.min_y, box_b.max_y)
    touches = _touches(box_a, box_b)
    contains = _contains(box_a, box_b) or _contains(box_b, box_a)

    return ComponentRelationship(
        component_a_id=component_a.component_id,
        component_b_id=component_b.component_id,
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
        edge_distance=hypot(horizontal_gap, vertical_gap),
        centroid_distance=hypot(
            component_a.centroid_x - component_b.centroid_x,
            component_a.centroid_y - component_b.centroid_y,
        ),
        x_overlap=x_overlap,
        y_overlap=y_overlap,
        x_overlap_ratio=_overlap_ratio(x_overlap, box_a.width, box_b.width),
        y_overlap_ratio=_overlap_ratio(y_overlap, box_a.height, box_b.height),
        area_ratio=_ratio(component_a.area, component_b.area),
        width_ratio=_ratio(box_a.width, box_b.width),
        height_ratio=_ratio(box_a.height, box_b.height),
        top_delta=abs(box_a.min_y - box_b.min_y),
        bottom_delta=abs(box_a.max_y - box_b.max_y),
        left_delta=abs(box_a.min_x - box_b.min_x),
        right_delta=abs(box_a.max_x - box_b.max_x),
        touches=touches,
        contains=contains,
        horizontal_adjacent=horizontal_gap > 0 and vertical_gap == 0,
        vertical_adjacent=vertical_gap > 0 and horizontal_gap == 0,
    )


def _axis_gap(a_min: int, a_max: int, b_min: int, b_max: int) -> int:
    if a_max < b_min:
        return b_min - a_max - 1
    if b_max < a_min:
        return a_min - b_max - 1
    return 0


def _axis_overlap(a_min: int, a_max: int, b_min: int, b_max: int) -> int:
    overlap_min = max(a_min, b_min)
    overlap_max = min(a_max, b_max)
    if overlap_max < overlap_min:
        return 0
    return overlap_max - overlap_min + 1


def _overlap_ratio(overlap: int, a_size: int, b_size: int) -> float:
    return overlap / min(a_size, b_size)


def _ratio(a_value: int, b_value: int) -> float:
    return min(a_value, b_value) / max(a_value, b_value)


def _touches(box_a: BoundingBox, box_b: BoundingBox) -> bool:
    horizontal_gap = _axis_gap(box_a.min_x, box_a.max_x, box_b.min_x, box_b.max_x)
    vertical_gap = _axis_gap(box_a.min_y, box_a.max_y, box_b.min_y, box_b.max_y)
    return horizontal_gap == 0 and vertical_gap == 0


def _contains(container: BoundingBox, contained: BoundingBox) -> bool:
    return (
        container.min_x <= contained.min_x
        and container.min_y <= contained.min_y
        and container.max_x >= contained.max_x
        and container.max_y >= contained.max_y
    )
