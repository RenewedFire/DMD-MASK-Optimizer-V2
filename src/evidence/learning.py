from __future__ import annotations

from dataclasses import dataclass

from src.evidence.evaluation import _binary_pixels, _box_overlap_scores, _human_box, _match_boxes
from src.frames import PixelMatrix
from src.spatial import BoundingBox


@dataclass(frozen=True)
class LearnedRegionTemplate:
    dump_filename: str
    bounding_box: BoundingBox
    support_count: int
    activation_count: int
    matched_activation_count: int

    @property
    def precision(self) -> float:
        if self.activation_count == 0:
            return 0.0
        return self.matched_activation_count / self.activation_count


@dataclass(frozen=True)
class LayoutPriorOptions:
    cluster_threshold: float = 0.50
    min_support_count: int = 3
    max_templates_per_frame: int = 2
    min_occupancy_ratio: float = 0.45
    min_activation_count: int = 1
    min_precision: float = 0.70


@dataclass(frozen=True)
class LayoutPriorModel:
    templates: tuple[LearnedRegionTemplate, ...]
    options: LayoutPriorOptions = LayoutPriorOptions()

    def predict_boxes(
        self,
        dump_filename: str,
        binary_pixels: PixelMatrix,
    ) -> tuple[BoundingBox, ...]:
        ranked: list[tuple[float, BoundingBox]] = []
        for template in self.templates:
            if template.dump_filename != dump_filename:
                continue
            occupancy = _occupancy_ratio(binary_pixels, template.bounding_box)
            if occupancy < self.options.min_occupancy_ratio:
                continue
            if template.activation_count < self.options.min_activation_count:
                continue
            if template.precision < self.options.min_precision:
                continue
            box_area = template.bounding_box.width * template.bounding_box.height
            score = (
                template.support_count
                * template.precision
                * occupancy
                * (1 + box_area / 4096)
            )
            ranked.append((score, template.bounding_box))

        return tuple(
            box
            for _score, box in sorted(ranked, key=lambda item: item[0], reverse=True)[
                : self.options.max_templates_per_frame
            ]
        )


@dataclass(frozen=True)
class _TrainingFrame:
    binary_pixels: PixelMatrix
    human_boxes: tuple[BoundingBox, ...]


def train_layout_prior_model(
    export_payload: dict[str, object],
    *,
    options: LayoutPriorOptions = LayoutPriorOptions(),
    exclude_frame_ids: tuple[int, ...] = (),
    dump_filename: str | None = None,
) -> LayoutPriorModel:
    excluded = set(exclude_frame_ids)
    templates: list[LearnedRegionTemplate] = []
    for dump in export_payload["dumps"]:
        if dump_filename is not None and dump["filename"] != dump_filename:
            continue
        training_frames = [
            evidence_frame
            for evidence_frame in dump["evidence_frames"]
            if evidence_frame["id"] not in excluded
        ]
        training_records = [
            _TrainingFrame(
                binary_pixels=_binary_pixels(evidence_frame["frame"]["pixels"]),
                human_boxes=tuple(_human_box(region) for region in evidence_frame["regions"]),
            )
            for evidence_frame in training_frames
        ]
        boxes = [
            _human_box(region)
            for evidence_frame in training_frames
            for region in evidence_frame["regions"]
        ]
        for cluster in _cluster_boxes(boxes, options.cluster_threshold):
            if len(cluster) < options.min_support_count:
                continue
            box = _average_box(cluster)
            activation_count, matched_activation_count = _template_reliability(
                training_records,
                box,
                options.min_occupancy_ratio,
            )
            templates.append(
                LearnedRegionTemplate(
                    dump_filename=dump["filename"],
                    bounding_box=box,
                    support_count=len(cluster),
                    activation_count=activation_count,
                    matched_activation_count=matched_activation_count,
                )
            )

    return LayoutPriorModel(templates=tuple(templates), options=options)


def _template_reliability(
    training_records: list[_TrainingFrame],
    box: BoundingBox,
    min_occupancy_ratio: float,
) -> tuple[int, int]:
    activation_count = 0
    matched_activation_count = 0
    for record in training_records:
        if _occupancy_ratio(record.binary_pixels, box) < min_occupancy_ratio:
            continue
        activation_count += 1
        if _match_boxes(record.human_boxes, (box,)):
            matched_activation_count += 1
    return activation_count, matched_activation_count


def _cluster_boxes(
    boxes: list[BoundingBox],
    threshold: float,
) -> tuple[tuple[BoundingBox, ...], ...]:
    clusters: list[list[BoundingBox]] = []
    cluster_boxes: list[BoundingBox] = []
    for box in boxes:
        best_index: int | None = None
        best_score = 0.0
        for index, cluster_box in enumerate(cluster_boxes):
            iou, first_coverage, second_coverage = _box_overlap_scores(box, cluster_box)
            score = max(iou, min(first_coverage, second_coverage))
            if score > best_score:
                best_index = index
                best_score = score
        if best_index is not None and best_score >= threshold:
            clusters[best_index].append(box)
            cluster_boxes[best_index] = _average_box(clusters[best_index])
            continue
        clusters.append([box])
        cluster_boxes.append(box)

    return tuple(tuple(cluster) for cluster in clusters)


def _average_box(boxes: list[BoundingBox]) -> BoundingBox:
    count = len(boxes)
    return BoundingBox(
        min_x=round(sum(box.min_x for box in boxes) / count),
        min_y=round(sum(box.min_y for box in boxes) / count),
        max_x=round(sum(box.max_x for box in boxes) / count),
        max_y=round(sum(box.max_y for box in boxes) / count),
    )


def _occupancy_ratio(binary_pixels: PixelMatrix, box: BoundingBox) -> float:
    height = len(binary_pixels)
    width = len(binary_pixels[0]) if height else 0
    if not height or not width:
        return 0.0
    min_x = max(0, box.min_x)
    min_y = max(0, box.min_y)
    max_x = min(width - 1, box.max_x)
    max_y = min(height - 1, box.max_y)
    if max_x < min_x or max_y < min_y:
        return 0.0
    lit_count = sum(
        binary_pixels[y][x]
        for y in range(min_y, max_y + 1)
        for x in range(min_x, max_x + 1)
    )
    return lit_count / ((max_x - min_x + 1) * (max_y - min_y + 1))
