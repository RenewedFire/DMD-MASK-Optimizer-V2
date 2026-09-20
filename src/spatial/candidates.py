from __future__ import annotations

from dataclasses import dataclass

from src.spatial.components import BoundingBox, LitComponent
from src.spatial.relationships import ComponentRelationship


DEFAULT_CANDIDATE_THRESHOLDS = (1, 2, 3)


@dataclass(frozen=True)
class CandidateCompositeBox:
    candidate_id: int
    threshold: int
    component_ids: tuple[int, ...]
    bounding_box: BoundingBox
    evidence_pairs: tuple[tuple[int, int], ...]

    @property
    def component_count(self) -> int:
        return len(self.component_ids)


def generate_candidate_boxes(
    components: tuple[LitComponent, ...],
    relationships: tuple[ComponentRelationship, ...],
    thresholds: tuple[int, ...] = DEFAULT_CANDIDATE_THRESHOLDS,
) -> tuple[CandidateCompositeBox, ...]:
    components_by_id = {component.component_id: component for component in components}
    candidates: list[CandidateCompositeBox] = []
    seen_pairs: set[tuple[int, int]] = set()

    for threshold in thresholds:
        for relationship in relationships:
            if not _supports_candidate_connection(relationship, threshold):
                continue
            component_ids = tuple(sorted((relationship.component_a_id, relationship.component_b_id)))
            if component_ids in seen_pairs:
                continue
            seen_pairs.add(component_ids)
            group_components = tuple(components_by_id[component_id] for component_id in component_ids)
            candidates.append(
                CandidateCompositeBox(
                    candidate_id=len(candidates),
                    threshold=threshold,
                    component_ids=component_ids,
                    bounding_box=_union_box(group_components),
                    evidence_pairs=(component_ids,),
                )
            )

    return tuple(candidates)


def candidate_boxes_to_payload(
    candidates: tuple[CandidateCompositeBox, ...],
) -> list[dict[str, object]]:
    return [
        {
            "candidate_id": candidate.candidate_id,
            "threshold": candidate.threshold,
            "component_ids": list(candidate.component_ids),
            "component_count": candidate.component_count,
            "bounding_box": {
                "min_x": candidate.bounding_box.min_x,
                "min_y": candidate.bounding_box.min_y,
                "max_x": candidate.bounding_box.max_x,
                "max_y": candidate.bounding_box.max_y,
                "width": candidate.bounding_box.width,
                "height": candidate.bounding_box.height,
            },
            "evidence_pairs": [
                {"component_a_id": component_a_id, "component_b_id": component_b_id}
                for component_a_id, component_b_id in candidate.evidence_pairs
            ],
        }
        for candidate in candidates
    ]


def _supports_candidate_connection(
    relationship: ComponentRelationship,
    threshold: int,
) -> bool:
    if relationship.edge_distance > threshold:
        return False
    return (
        relationship.touches
        or relationship.x_overlap > 0
        or relationship.y_overlap > 0
        or relationship.edge_distance <= 1
    )


def _union_box(components: tuple[LitComponent, ...]) -> BoundingBox:
    return BoundingBox(
        min_x=min(component.bounding_box.min_x for component in components),
        min_y=min(component.bounding_box.min_y for component in components),
        max_x=max(component.bounding_box.max_x for component in components),
        max_y=max(component.bounding_box.max_y for component in components),
    )
