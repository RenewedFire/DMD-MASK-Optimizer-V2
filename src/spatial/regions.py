from __future__ import annotations

from dataclasses import dataclass

from src.spatial.candidates import CandidateCompositeBox
from src.spatial.components import BoundingBox, LitComponent


@dataclass(frozen=True)
class SpatialRegion:
    region_id: int
    component_ids: tuple[int, ...]
    bounding_box: BoundingBox
    area: int
    occupancy_ratio: float
    candidate_ids: tuple[int, ...]
    evidence_pairs: tuple[tuple[int, int], ...]

    @property
    def component_count(self) -> int:
        return len(self.component_ids)


def discover_spatial_regions(
    components: tuple[LitComponent, ...],
    candidates: tuple[CandidateCompositeBox, ...],
    *,
    max_threshold: int = 3,
) -> tuple[SpatialRegion, ...]:
    components_by_id = {component.component_id: component for component in components}
    adjacency: dict[int, set[int]] = {component.component_id: set() for component in components}
    candidate_ids_by_pair: dict[tuple[int, int], list[int]] = {}

    for candidate in candidates:
        if candidate.threshold > max_threshold or len(candidate.component_ids) != 2:
            continue
        left, right = candidate.component_ids
        if left not in adjacency or right not in adjacency:
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
        candidate_ids_by_pair.setdefault((left, right), []).append(candidate.candidate_id)

    regions: list[SpatialRegion] = []
    visited: set[int] = set()
    for component in components:
        if component.component_id in visited:
            continue
        group_ids = _collect_group(component.component_id, adjacency, visited)
        group_components = tuple(components_by_id[component_id] for component_id in group_ids)
        evidence_pairs = tuple(
            pair for pair in sorted(candidate_ids_by_pair) if pair[0] in group_ids and pair[1] in group_ids
        )
        candidate_ids = tuple(
            candidate_id
            for pair in evidence_pairs
            for candidate_id in candidate_ids_by_pair[pair]
        )
        regions.append(
            SpatialRegion(
                region_id=len(regions),
                component_ids=group_ids,
                bounding_box=_union_box(group_components),
                area=sum(item.area for item in group_components),
                occupancy_ratio=_occupancy_ratio(group_components),
                candidate_ids=candidate_ids,
                evidence_pairs=evidence_pairs,
            )
        )

    return tuple(regions)


def regions_to_payload(regions: tuple[SpatialRegion, ...]) -> list[dict[str, object]]:
    return [
        {
            "region_id": region.region_id,
            "component_ids": list(region.component_ids),
            "component_count": region.component_count,
            "area": region.area,
            "occupancy_ratio": region.occupancy_ratio,
            "candidate_ids": list(region.candidate_ids),
            "bounding_box": {
                "min_x": region.bounding_box.min_x,
                "min_y": region.bounding_box.min_y,
                "max_x": region.bounding_box.max_x,
                "max_y": region.bounding_box.max_y,
                "width": region.bounding_box.width,
                "height": region.bounding_box.height,
            },
            "evidence_pairs": [
                {"component_a_id": left, "component_b_id": right}
                for left, right in region.evidence_pairs
            ],
        }
        for region in regions
    ]


def _collect_group(
    start_id: int,
    adjacency: dict[int, set[int]],
    visited: set[int],
) -> tuple[int, ...]:
    stack = [start_id]
    group: list[int] = []
    visited.add(start_id)
    while stack:
        component_id = stack.pop()
        group.append(component_id)
        for neighbor_id in sorted(adjacency[component_id], reverse=True):
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)
            stack.append(neighbor_id)
    return tuple(sorted(group))


def _union_box(components: tuple[LitComponent, ...]) -> BoundingBox:
    return BoundingBox(
        min_x=min(component.bounding_box.min_x for component in components),
        min_y=min(component.bounding_box.min_y for component in components),
        max_x=max(component.bounding_box.max_x for component in components),
        max_y=max(component.bounding_box.max_y for component in components),
    )


def _occupancy_ratio(components: tuple[LitComponent, ...]) -> float:
    box = _union_box(components)
    return sum(component.area for component in components) / (box.width * box.height)
