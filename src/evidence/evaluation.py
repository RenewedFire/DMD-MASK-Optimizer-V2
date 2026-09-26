from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable

from src.frames import PixelMatrix
from src.spatial import (
    BoundingBox,
    find_component_relationships,
    find_lit_components,
    find_region_split_evidence,
    generate_candidate_boxes,
    discover_spatial_regions,
    refine_spatial_regions,
)


@dataclass(frozen=True)
class DetectorOptions:
    max_candidate_threshold: int = 3
    max_corridor_occupancy_ratio: float = 0.03
    min_negative_space_ratio: float = 0.20
    min_band_height: int = 2
    min_band_width: int = 6


@dataclass(frozen=True)
class RegionMatch:
    human_index: int
    detected_index: int
    score: float
    iou: float
    human_coverage: float
    detected_coverage: float


@dataclass(frozen=True)
class EvaluationFrameResult:
    filename: str
    source_frame_index: int
    descriptor: str
    human_count: int
    detected_count: int
    matched_count: int
    missed_count: int
    extra_count: int
    mean_match_score: float
    matches: tuple[RegionMatch, ...]

    @property
    def alignment_score(self) -> float:
        if self.human_count == 0 and self.detected_count == 0:
            return 1.0
        denominator = self.human_count + self.detected_count
        if denominator == 0:
            return 0.0
        return 2 * self.matched_count / denominator


@dataclass(frozen=True)
class EvaluationReport:
    options: DetectorOptions
    frame_count: int
    human_region_count: int
    detected_region_count: int
    matched_region_count: int
    missed_region_count: int
    extra_region_count: int
    mean_alignment_score: float
    mean_match_score: float
    frame_results: tuple[EvaluationFrameResult, ...]

    def summary(self) -> dict[str, object]:
        return {
            "options": {
                "max_candidate_threshold": self.options.max_candidate_threshold,
                "max_corridor_occupancy_ratio": self.options.max_corridor_occupancy_ratio,
                "min_negative_space_ratio": self.options.min_negative_space_ratio,
                "min_band_height": self.options.min_band_height,
                "min_band_width": self.options.min_band_width,
            },
            "frame_count": self.frame_count,
            "human_region_count": self.human_region_count,
            "detected_region_count": self.detected_region_count,
            "matched_region_count": self.matched_region_count,
            "missed_region_count": self.missed_region_count,
            "extra_region_count": self.extra_region_count,
            "mean_alignment_score": self.mean_alignment_score,
            "mean_match_score": self.mean_match_score,
            "worst_frames": [
                {
                    "filename": frame.filename,
                    "source_frame_index": frame.source_frame_index,
                    "descriptor": frame.descriptor,
                    "human_count": frame.human_count,
                    "detected_count": frame.detected_count,
                    "matched_count": frame.matched_count,
                    "missed_count": frame.missed_count,
                    "extra_count": frame.extra_count,
                    "alignment_score": frame.alignment_score,
                    "mean_match_score": frame.mean_match_score,
                }
                for frame in sorted(
                    self.frame_results,
                    key=lambda item: (item.alignment_score, item.mean_match_score),
                )[:10]
            ],
        }


@dataclass(frozen=True)
class FailurePattern:
    category: str
    count: int
    examples: tuple[dict[str, object], ...]


def evaluate_evidence_export(
    export_path: str | Path,
    options: DetectorOptions = DetectorOptions(),
) -> EvaluationReport:
    payload = json.loads(Path(export_path).read_text(encoding="utf-8"))
    frame_results: list[EvaluationFrameResult] = []

    for dump in payload["dumps"]:
        for evidence_frame in dump["evidence_frames"]:
            human_boxes = tuple(_human_box(region) for region in evidence_frame["regions"])
            detected_boxes = detect_refined_region_boxes(
                _binary_pixels(evidence_frame["frame"]["pixels"]),
                options,
            )
            frame_results.append(
                _evaluate_frame(
                    filename=dump["filename"],
                    source_frame_index=evidence_frame["source_frame_index"],
                    descriptor=evidence_frame["descriptor"],
                    human_boxes=human_boxes,
                    detected_boxes=detected_boxes,
                )
            )

    return _build_report(options, frame_results)


def analyze_failure_patterns(
    export_path: str | Path,
    options: DetectorOptions = DetectorOptions(),
) -> tuple[FailurePattern, ...]:
    payload = json.loads(Path(export_path).read_text(encoding="utf-8"))
    buckets: dict[str, list[dict[str, object]]] = {}

    for dump in payload["dumps"]:
        for evidence_frame in dump["evidence_frames"]:
            human_boxes = tuple(_human_box(region) for region in evidence_frame["regions"])
            detected_boxes = detect_refined_region_boxes(
                _binary_pixels(evidence_frame["frame"]["pixels"]),
                options,
            )
            matches = _match_boxes(human_boxes, detected_boxes)
            matched_human_indexes = {match.human_index for match in matches}
            for human_index, human_box in enumerate(human_boxes):
                if human_index in matched_human_indexes:
                    continue
                category = _classify_missed_region(human_box, detected_boxes)
                buckets.setdefault(category, []).append(
                    {
                        "filename": dump["filename"],
                        "source_frame_index": evidence_frame["source_frame_index"],
                        "descriptor": evidence_frame["descriptor"],
                        "human_index": human_index,
                        "human_box": _box_payload(human_box),
                        "detected_count": len(detected_boxes),
                    }
                )

    return tuple(
        FailurePattern(
            category=category,
            count=len(examples),
            examples=tuple(examples[:8]),
        )
        for category, examples in sorted(
            buckets.items(),
            key=lambda item: len(item[1]),
            reverse=True,
        )
    )


def optimize_detector_options(
    export_path: str | Path,
    option_grid: Iterable[DetectorOptions] | None = None,
) -> tuple[EvaluationReport, ...]:
    grid = tuple(option_grid) if option_grid is not None else _default_option_grid()
    reports = tuple(evaluate_evidence_export(export_path, options) for options in grid)
    return tuple(
        sorted(
            reports,
            key=lambda report: (
                report.mean_alignment_score,
                report.mean_match_score,
                -report.extra_region_count,
            ),
            reverse=True,
        )
    )


def detect_refined_region_boxes(
    binary_pixels: PixelMatrix,
    options: DetectorOptions = DetectorOptions(),
) -> tuple[BoundingBox, ...]:
    components = find_lit_components(binary_pixels)
    relationships = find_component_relationships(components)
    candidates = generate_candidate_boxes(components, relationships)
    regions = discover_spatial_regions(
        components,
        candidates,
        max_threshold=options.max_candidate_threshold,
    )
    split_evidence = find_region_split_evidence(
        components,
        regions,
        binary_pixels=binary_pixels,
        max_corridor_occupancy_ratio=options.max_corridor_occupancy_ratio,
        min_negative_space_ratio=options.min_negative_space_ratio,
        min_band_height=options.min_band_height,
        min_band_width=options.min_band_width,
    )
    refined_regions = refine_spatial_regions(regions, split_evidence)
    return tuple(region.bounding_box for region in refined_regions)


def _evaluate_frame(
    *,
    filename: str,
    source_frame_index: int,
    descriptor: str,
    human_boxes: tuple[BoundingBox, ...],
    detected_boxes: tuple[BoundingBox, ...],
) -> EvaluationFrameResult:
    matches = _match_boxes(human_boxes, detected_boxes)
    mean_match_score = (
        sum(match.score for match in matches) / len(matches)
        if matches
        else 0.0
    )
    return EvaluationFrameResult(
        filename=filename,
        source_frame_index=source_frame_index,
        descriptor=descriptor,
        human_count=len(human_boxes),
        detected_count=len(detected_boxes),
        matched_count=len(matches),
        missed_count=len(human_boxes) - len(matches),
        extra_count=len(detected_boxes) - len(matches),
        mean_match_score=mean_match_score,
        matches=matches,
    )


def _match_boxes(
    human_boxes: tuple[BoundingBox, ...],
    detected_boxes: tuple[BoundingBox, ...],
) -> tuple[RegionMatch, ...]:
    candidates: list[RegionMatch] = []
    for human_index, human_box in enumerate(human_boxes):
        for detected_index, detected_box in enumerate(detected_boxes):
            iou, human_coverage, detected_coverage = _box_overlap_scores(
                human_box,
                detected_box,
            )
            containment_score = min(human_coverage, detected_coverage)
            score = max(iou, containment_score)
            if iou < 0.45 and containment_score < 0.72:
                continue
            candidates.append(
                RegionMatch(
                    human_index=human_index,
                    detected_index=detected_index,
                    score=score,
                    iou=iou,
                    human_coverage=human_coverage,
                    detected_coverage=detected_coverage,
                )
            )

    matches: list[RegionMatch] = []
    used_human: set[int] = set()
    used_detected: set[int] = set()
    for match in sorted(candidates, key=lambda item: item.score, reverse=True):
        if match.human_index in used_human or match.detected_index in used_detected:
            continue
        used_human.add(match.human_index)
        used_detected.add(match.detected_index)
        matches.append(match)
    return tuple(sorted(matches, key=lambda item: item.human_index))


def _classify_missed_region(
    human_box: BoundingBox,
    detected_boxes: tuple[BoundingBox, ...],
) -> str:
    if not detected_boxes:
        return "no detected regions"

    contained_detected = [
        detected_box
        for detected_box in detected_boxes
        if _contains_box(human_box, detected_box)
    ]
    containing_detected = [
        detected_box
        for detected_box in detected_boxes
        if _contains_box(detected_box, human_box)
    ]
    overlapping_detected = [
        detected_box
        for detected_box in detected_boxes
        if _box_overlap_scores(human_box, detected_box)[1] > 0
    ]

    if len(contained_detected) >= 2:
        return "under-grouped pieces inside human region"
    if containing_detected:
        smallest_container = min(containing_detected, key=_box_area)
        area_ratio = _box_area(smallest_container) / _box_area(human_box)
        if area_ratio >= 2.5:
            return "missing child region inside broad container"
        return "over-grouped detector region contains human region"
    if not overlapping_detected:
        if human_box.width >= 90 or human_box.height >= 24:
            return "missing broad container/logical region"
        return "missing isolated human region"
    if human_box.width >= 32 and human_box.height <= 14:
        return "internal-gap text/row grouping mismatch"
    if human_box.width >= 45 and human_box.height >= 18:
        return "irregular object or container ROI mismatch"
    return "partial-overlap geometry mismatch"


def _build_report(
    options: DetectorOptions,
    frame_results: list[EvaluationFrameResult],
) -> EvaluationReport:
    frame_count = len(frame_results)
    matched_region_count = sum(frame.matched_count for frame in frame_results)
    return EvaluationReport(
        options=options,
        frame_count=frame_count,
        human_region_count=sum(frame.human_count for frame in frame_results),
        detected_region_count=sum(frame.detected_count for frame in frame_results),
        matched_region_count=matched_region_count,
        missed_region_count=sum(frame.missed_count for frame in frame_results),
        extra_region_count=sum(frame.extra_count for frame in frame_results),
        mean_alignment_score=(
            sum(frame.alignment_score for frame in frame_results) / frame_count
            if frame_count
            else 0.0
        ),
        mean_match_score=(
            sum(
                match.score
                for frame in frame_results
                for match in frame.matches
            )
            / matched_region_count
            if matched_region_count
            else 0.0
        ),
        frame_results=tuple(frame_results),
    )


def _box_overlap_scores(
    first: BoundingBox,
    second: BoundingBox,
) -> tuple[float, float, float]:
    intersection_width = max(
        0,
        min(first.max_x, second.max_x) - max(first.min_x, second.min_x) + 1,
    )
    intersection_height = max(
        0,
        min(first.max_y, second.max_y) - max(first.min_y, second.min_y) + 1,
    )
    intersection_area = intersection_width * intersection_height
    first_area = _box_area(first)
    second_area = _box_area(second)
    union_area = first_area + second_area - intersection_area
    if union_area == 0:
        return 0.0, 0.0, 0.0
    return (
        intersection_area / union_area,
        intersection_area / first_area if first_area else 0.0,
        intersection_area / second_area if second_area else 0.0,
    )


def _contains_box(container: BoundingBox, contained: BoundingBox) -> bool:
    return (
        container.min_x <= contained.min_x
        and container.min_y <= contained.min_y
        and container.max_x >= contained.max_x
        and container.max_y >= contained.max_y
    )


def _box_payload(box: BoundingBox) -> dict[str, int]:
    return {
        "x": box.min_x,
        "y": box.min_y,
        "width": box.width,
        "height": box.height,
    }


def _box_area(box: BoundingBox) -> int:
    return box.width * box.height


def _human_box(region: dict[str, int]) -> BoundingBox:
    return BoundingBox(
        min_x=region["x"],
        min_y=region["y"],
        max_x=region["x"] + region["width"] - 1,
        max_y=region["y"] + region["height"] - 1,
    )


def _binary_pixels(pixels: list[list[int]]) -> PixelMatrix:
    return tuple(tuple(1 if value else 0 for value in row) for row in pixels)


def _default_option_grid() -> tuple[DetectorOptions, ...]:
    return tuple(
        DetectorOptions(
            max_candidate_threshold=max_threshold,
            max_corridor_occupancy_ratio=corridor_ratio,
            min_negative_space_ratio=negative_ratio,
            min_band_height=min_band_height,
            min_band_width=min_band_width,
        )
        for max_threshold in (2, 3)
        for corridor_ratio in (0.02, 0.03, 0.05)
        for negative_ratio in (0.20, 0.25, 0.30)
        for min_band_height in (2, 3)
        for min_band_width in (5, 6, 8)
    )
