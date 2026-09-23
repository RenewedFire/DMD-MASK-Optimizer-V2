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


@dataclass(frozen=True)
class RegionSplitBand:
    band_id: int
    component_ids: tuple[int, ...]
    bounding_box: BoundingBox
    area: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    @property
    def component_count(self) -> int:
        return len(self.component_ids)


@dataclass(frozen=True)
class RegionSplitEvidence:
    split_id: int
    region_id: int
    axis: str
    reason: str
    corridor_rows: tuple[int, ...]
    bands: tuple[RegionSplitBand, ...]
    crossing_component_ids: tuple[int, ...]

    @property
    def band_count(self) -> int:
        return len(self.bands)


@dataclass(frozen=True)
class RefinedSpatialRegion:
    refined_region_id: int
    source_region_id: int
    source_split_id: int | None
    source_band_id: int | None
    refinement_reason: str
    component_ids: tuple[int, ...]
    bounding_box: BoundingBox
    area: int

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


def find_region_split_evidence(
    components: tuple[LitComponent, ...],
    regions: tuple[SpatialRegion, ...],
    *,
    binary_pixels: tuple[tuple[int, ...], ...] | None = None,
    max_corridor_occupancy_ratio: float = 0.03,
    min_negative_space_ratio: float = 0.25,
    min_band_height: int = 2,
    min_band_width: int = 6,
) -> tuple[RegionSplitEvidence, ...]:
    components_by_id = {component.component_id: component for component in components}
    split_evidence: list[RegionSplitEvidence] = []

    for region in regions:
        region_components = tuple(components_by_id[component_id] for component_id in region.component_ids)
        if region.component_count >= 2:
            bands, corridor_rows, crossing_ids = _horizontal_split_bands(
                region_components,
                region.bounding_box,
                max_corridor_occupancy_ratio=max_corridor_occupancy_ratio,
                min_band_height=min_band_height,
            )
            if len(bands) < 2:
                vertical_bands, corridor_columns, vertical_crossing_ids = _vertical_split_bands(
                    region_components,
                    region.bounding_box,
                    max_corridor_occupancy_ratio=max_corridor_occupancy_ratio,
                    min_band_width=min_band_width,
                )
                if len(vertical_bands) >= 2:
                    split_evidence.append(
                        RegionSplitEvidence(
                            split_id=len(split_evidence),
                            region_id=region.region_id,
                            axis="vertical",
                            reason="internal low-occupancy column corridor",
                            corridor_rows=corridor_columns,
                            bands=vertical_bands,
                            crossing_component_ids=vertical_crossing_ids,
                        )
                    )
            else:
                split_evidence.append(
                    RegionSplitEvidence(
                        split_id=len(split_evidence),
                        region_id=region.region_id,
                        axis="horizontal",
                        reason="internal low-occupancy row corridor",
                        corridor_rows=corridor_rows,
                        bands=bands,
                        crossing_component_ids=crossing_ids,
                    )
                )
                for band in bands:
                    vertical_bands, corridor_columns, vertical_crossing_ids = _vertical_split_bands(
                        region_components,
                        band.bounding_box,
                        max_corridor_occupancy_ratio=max_corridor_occupancy_ratio,
                        min_band_width=min_band_width,
                    )
                    if len(vertical_bands) < 2:
                        continue
                    split_evidence.append(
                        RegionSplitEvidence(
                            split_id=len(split_evidence),
                            region_id=region.region_id,
                            axis="vertical",
                            reason="vertical corridor inside horizontal band",
                            corridor_rows=corridor_columns,
                            bands=vertical_bands,
                            crossing_component_ids=vertical_crossing_ids,
                        )
                    )

        if binary_pixels is None:
            continue
        negative_bands = _negative_space_horizontal_bands(
            binary_pixels,
            region.bounding_box,
            min_negative_space_ratio=min_negative_space_ratio,
            min_band_height=min_band_height,
        )
        if len(negative_bands) >= 1:
            split_evidence.append(
                RegionSplitEvidence(
                    split_id=len(split_evidence),
                    region_id=region.region_id,
                    axis="horizontal",
                    reason="negative-space horizontal band",
                    corridor_rows=(),
                    bands=negative_bands,
                    crossing_component_ids=(),
                )
            )
            for band in negative_bands:
                vertical_bands, corridor_columns, vertical_crossing_ids = _vertical_split_bands(
                    region_components,
                    band.bounding_box,
                    max_corridor_occupancy_ratio=max_corridor_occupancy_ratio,
                    min_band_width=min_band_width,
                )
                if len(vertical_bands) < 2:
                    continue
                split_evidence.append(
                    RegionSplitEvidence(
                        split_id=len(split_evidence),
                        region_id=region.region_id,
                        axis="vertical",
                        reason="vertical corridor inside negative-space band",
                        corridor_rows=corridor_columns,
                        bands=vertical_bands,
                        crossing_component_ids=vertical_crossing_ids,
                    )
                )

    return tuple(split_evidence)


def refine_spatial_regions(
    regions: tuple[SpatialRegion, ...],
    split_evidence: tuple[RegionSplitEvidence, ...],
) -> tuple[RefinedSpatialRegion, ...]:
    splits_by_region: dict[int, list[RegionSplitEvidence]] = {}
    for split in split_evidence:
        splits_by_region.setdefault(split.region_id, []).append(split)

    refined_regions: list[RefinedSpatialRegion] = []
    for region in regions:
        region_splits = splits_by_region.get(region.region_id, ())
        selected_split = _select_refinement_split(region, region_splits)
        if selected_split is None:
            refined_regions.append(
                RefinedSpatialRegion(
                    refined_region_id=len(refined_regions),
                    source_region_id=region.region_id,
                    source_split_id=None,
                    source_band_id=None,
                    refinement_reason="kept first-pass region",
                    component_ids=region.component_ids,
                    bounding_box=region.bounding_box,
                    area=region.area,
                )
            )
            continue

        for band in selected_split.bands:
            nested_vertical_split = _select_nested_vertical_split(band, region_splits)
            if nested_vertical_split is not None:
                for nested_band in nested_vertical_split.bands:
                    refined_regions.append(
                        RefinedSpatialRegion(
                            refined_region_id=len(refined_regions),
                            source_region_id=region.region_id,
                            source_split_id=nested_vertical_split.split_id,
                            source_band_id=nested_band.band_id,
                            refinement_reason=nested_vertical_split.reason,
                            component_ids=nested_band.component_ids,
                            bounding_box=nested_band.bounding_box,
                            area=nested_band.area,
                        )
                    )
                continue

            refined_regions.append(
                RefinedSpatialRegion(
                    refined_region_id=len(refined_regions),
                    source_region_id=region.region_id,
                    source_split_id=selected_split.split_id,
                    source_band_id=band.band_id,
                    refinement_reason=selected_split.reason,
                    component_ids=band.component_ids,
                    bounding_box=band.bounding_box,
                    area=band.area,
                )
            )

    return tuple(refined_regions)


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


def refined_regions_to_payload(
    refined_regions: tuple[RefinedSpatialRegion, ...],
) -> list[dict[str, object]]:
    return [
        {
            "refined_region_id": region.refined_region_id,
            "source_region_id": region.source_region_id,
            "source_split_id": region.source_split_id,
            "source_band_id": region.source_band_id,
            "refinement_reason": region.refinement_reason,
            "component_ids": list(region.component_ids),
            "component_count": region.component_count,
            "area": region.area,
            "bounding_box": {
                "min_x": region.bounding_box.min_x,
                "min_y": region.bounding_box.min_y,
                "max_x": region.bounding_box.max_x,
                "max_y": region.bounding_box.max_y,
                "width": region.bounding_box.width,
                "height": region.bounding_box.height,
            },
        }
        for region in refined_regions
    ]


def region_split_evidence_to_payload(
    split_evidence: tuple[RegionSplitEvidence, ...],
) -> list[dict[str, object]]:
    return [
        {
            "split_id": split.split_id,
            "region_id": split.region_id,
            "axis": split.axis,
            "reason": split.reason,
            "corridor_rows": list(split.corridor_rows),
            "band_count": split.band_count,
            "crossing_component_ids": list(split.crossing_component_ids),
            "bands": [
                {
                    "band_id": band.band_id,
                    "component_ids": list(band.component_ids),
                    "component_count": band.component_count,
                    "area": band.area,
                    "x_min": band.x_min,
                    "x_max": band.x_max,
                    "y_min": band.y_min,
                    "y_max": band.y_max,
                    "bounding_box": {
                        "min_x": band.bounding_box.min_x,
                        "min_y": band.bounding_box.min_y,
                        "max_x": band.bounding_box.max_x,
                        "max_y": band.bounding_box.max_y,
                        "width": band.bounding_box.width,
                        "height": band.bounding_box.height,
                    },
                }
                for band in split.bands
            ],
        }
        for split in split_evidence
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


def _horizontal_split_bands(
    components: tuple[LitComponent, ...],
    region_box: BoundingBox,
    *,
    max_corridor_occupancy_ratio: float,
    min_band_height: int,
) -> tuple[tuple[RegionSplitBand, ...], tuple[int, ...], tuple[int, ...]]:
    pixels_by_y: dict[int, list[tuple[int, int, int]]] = {
        y: [] for y in range(region_box.min_y, region_box.max_y + 1)
    }
    for component in components:
        for x, y in component.pixels:
            if region_box.min_y <= y <= region_box.max_y:
                pixels_by_y[y].append((x, y, component.component_id))

    corridor_limit = max(1, int(region_box.width * max_corridor_occupancy_ratio))
    corridor_rows = tuple(
        y
        for y, pixels in pixels_by_y.items()
        if y not in {region_box.min_y, region_box.max_y} and len(pixels) <= corridor_limit
    )
    corridor_row_set = set(corridor_rows)

    row_bands: list[tuple[int, int]] = []
    band_start: int | None = None
    previous_y: int | None = None
    for y in range(region_box.min_y, region_box.max_y + 1):
        if y in corridor_row_set:
            if band_start is not None and previous_y is not None:
                row_bands.append((band_start, previous_y))
                band_start = None
            continue
        if band_start is None:
            band_start = y
        previous_y = y
    if band_start is not None and previous_y is not None:
        row_bands.append((band_start, previous_y))

    bands: list[RegionSplitBand] = []
    component_band_ids: dict[int, set[int]] = {}
    for y_min, y_max in row_bands:
        if y_max - y_min + 1 < min_band_height:
            continue
        band_pixels = [
            (x, y, component_id)
            for y in range(y_min, y_max + 1)
            for x, _, component_id in pixels_by_y[y]
        ]
        if not band_pixels:
            continue
        xs = [x for x, _, _ in band_pixels]
        ys = [y for _, y, _ in band_pixels]
        component_ids = tuple(sorted({component_id for _, _, component_id in band_pixels}))
        band_id = len(bands)
        for component_id in component_ids:
            component_band_ids.setdefault(component_id, set()).add(band_id)
        bands.append(
            RegionSplitBand(
                band_id=band_id,
                component_ids=component_ids,
                bounding_box=BoundingBox(
                    min_x=min(xs),
                    min_y=min(ys),
                    max_x=max(xs),
                    max_y=max(ys),
                ),
                area=len(band_pixels),
                x_min=min(xs),
                x_max=max(xs),
                y_min=y_min,
                y_max=y_max,
            )
        )

    crossing_ids = tuple(
        sorted(component_id for component_id, band_ids in component_band_ids.items() if len(band_ids) > 1)
    )
    return tuple(bands), corridor_rows, crossing_ids


def _vertical_split_bands(
    components: tuple[LitComponent, ...],
    region_box: BoundingBox,
    *,
    max_corridor_occupancy_ratio: float,
    min_band_width: int,
) -> tuple[tuple[RegionSplitBand, ...], tuple[int, ...], tuple[int, ...]]:
    pixels_by_x: dict[int, list[tuple[int, int, int]]] = {
        x: [] for x in range(region_box.min_x, region_box.max_x + 1)
    }
    for component in components:
        for x, y in component.pixels:
            if (
                region_box.min_x <= x <= region_box.max_x
                and region_box.min_y <= y <= region_box.max_y
            ):
                pixels_by_x[x].append((x, y, component.component_id))

    corridor_limit = max(1, int(region_box.height * max_corridor_occupancy_ratio))
    corridor_columns = tuple(
        x
        for x, pixels in pixels_by_x.items()
        if x not in {region_box.min_x, region_box.max_x} and len(pixels) <= corridor_limit
    )
    corridor_column_set = set(corridor_columns)

    column_bands: list[tuple[int, int]] = []
    band_start: int | None = None
    previous_x: int | None = None
    for x in range(region_box.min_x, region_box.max_x + 1):
        if x in corridor_column_set:
            if band_start is not None and previous_x is not None:
                column_bands.append((band_start, previous_x))
                band_start = None
            continue
        if band_start is None:
            band_start = x
        previous_x = x
    if band_start is not None and previous_x is not None:
        column_bands.append((band_start, previous_x))

    bands: list[RegionSplitBand] = []
    component_band_ids: dict[int, set[int]] = {}
    for x_min, x_max in column_bands:
        if x_max - x_min + 1 < min_band_width:
            continue
        band_pixels = [
            (x, y, component_id)
            for x in range(x_min, x_max + 1)
            for _, y, component_id in pixels_by_x[x]
        ]
        if not band_pixels:
            continue
        xs = [x for x, _, _ in band_pixels]
        ys = [y for _, y, _ in band_pixels]
        component_ids = tuple(sorted({component_id for _, _, component_id in band_pixels}))
        band_id = len(bands)
        for component_id in component_ids:
            component_band_ids.setdefault(component_id, set()).add(band_id)
        bands.append(
            RegionSplitBand(
                band_id=band_id,
                component_ids=component_ids,
                bounding_box=BoundingBox(
                    min_x=min(xs),
                    min_y=min(ys),
                    max_x=max(xs),
                    max_y=max(ys),
                ),
                area=len(band_pixels),
                x_min=x_min,
                x_max=x_max,
                y_min=min(ys),
                y_max=max(ys),
            )
        )

    crossing_ids = tuple(
        sorted(component_id for component_id, band_ids in component_band_ids.items() if len(band_ids) > 1)
    )
    return tuple(bands), corridor_columns, crossing_ids


def _negative_space_horizontal_bands(
    binary_pixels: tuple[tuple[int, ...], ...],
    region_box: BoundingBox,
    *,
    min_negative_space_ratio: float,
    min_band_height: int,
) -> tuple[RegionSplitBand, ...]:
    row_dark_pixels: dict[int, list[tuple[int, int]]] = {}
    dark_threshold = max(1, int(region_box.width * min_negative_space_ratio))
    for y in range(region_box.min_y, region_box.max_y + 1):
        dark_pixels = [
            (x, y)
            for x in range(region_box.min_x, region_box.max_x + 1)
            if binary_pixels[y][x] == 0
        ]
        if len(dark_pixels) >= dark_threshold:
            row_dark_pixels[y] = dark_pixels

    bands: list[RegionSplitBand] = []
    current_rows: list[int] = []
    previous_y: int | None = None
    for y in sorted(row_dark_pixels):
        if previous_y is not None and y > previous_y + 2:
            _append_negative_band(bands, current_rows, row_dark_pixels, min_band_height)
            current_rows = []
        current_rows.append(y)
        previous_y = y
    _append_negative_band(bands, current_rows, row_dark_pixels, min_band_height)

    return tuple(bands)


def _select_refinement_split(
    region: SpatialRegion,
    split_evidence: tuple[RegionSplitEvidence, ...] | list[RegionSplitEvidence],
) -> RegionSplitEvidence | None:
    eligible = [
        split
        for split in split_evidence
        if split.axis == "horizontal"
        and split.band_count >= 2
        and split.reason in {
            "negative-space horizontal band",
            "internal low-occupancy row corridor",
        }
    ]
    if not eligible:
        return None

    def score(split: RegionSplitEvidence) -> tuple[int, int, int]:
        total_box_area = sum(
            band.bounding_box.width * band.bounding_box.height for band in split.bands
        )
        return (total_box_area, split.band_count, -split.split_id)

    selected = max(eligible, key=score)
    if _looks_like_object_slices(region.bounding_box, selected):
        return None
    return selected


def _select_nested_vertical_split(
    band: RegionSplitBand,
    split_evidence: tuple[RegionSplitEvidence, ...] | list[RegionSplitEvidence],
) -> RegionSplitEvidence | None:
    if band.bounding_box.height > 10:
        return None
    if band.bounding_box.min_y < 16:
        return None

    candidates = [
        split
        for split in split_evidence
        if split.axis == "vertical"
        and split.band_count >= 2
        and _compatible_nested_vertical_band(band.bounding_box, _union_band_box(split.bands))
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda split: (split.band_count, -split.split_id))


def _looks_like_object_slices(region_box: BoundingBox, split: RegionSplitEvidence) -> bool:
    if split.band_count < 3:
        return False
    region_area = region_box.width * region_box.height
    split_area = sum(band.bounding_box.width * band.bounding_box.height for band in split.bands)
    if split_area / region_area > 0.65:
        return False
    broad_bands = [
        band for band in split.bands if band.bounding_box.width / region_box.width >= 0.72
    ]
    if len(broad_bands) < 3:
        return False
    overlap_pairs = 0
    for first, second in zip(broad_bands, broad_bands[1:]):
        overlap = _axis_overlap(
            first.bounding_box.min_x,
            first.bounding_box.max_x,
            second.bounding_box.min_x,
            second.bounding_box.max_x,
        )
        if overlap / min(first.bounding_box.width, second.bounding_box.width) >= 0.70:
            overlap_pairs += 1
    return overlap_pairs >= len(broad_bands) - 1


def _contains_box(container: BoundingBox, contained: BoundingBox) -> bool:
    return (
        container.min_x <= contained.min_x
        and container.min_y <= contained.min_y
        and container.max_x >= contained.max_x
        and container.max_y >= contained.max_y
    )


def _compatible_nested_vertical_band(parent_band: BoundingBox, vertical_band_box: BoundingBox) -> bool:
    if _contains_box(parent_band, vertical_band_box):
        return True
    return (
        vertical_band_box.min_y <= parent_band.min_y
        and vertical_band_box.max_y == parent_band.max_y
        and vertical_band_box.height <= parent_band.height + 5
        and _axis_overlap(
            parent_band.min_x,
            parent_band.max_x,
            vertical_band_box.min_x,
            vertical_band_box.max_x,
        ) / min(parent_band.width, vertical_band_box.width) >= 0.80
    )


def _union_band_box(bands: tuple[RegionSplitBand, ...]) -> BoundingBox:
    return BoundingBox(
        min_x=min(band.bounding_box.min_x for band in bands),
        min_y=min(band.bounding_box.min_y for band in bands),
        max_x=max(band.bounding_box.max_x for band in bands),
        max_y=max(band.bounding_box.max_y for band in bands),
    )


def _axis_overlap(a_min: int, a_max: int, b_min: int, b_max: int) -> int:
    overlap_min = max(a_min, b_min)
    overlap_max = min(a_max, b_max)
    if overlap_max < overlap_min:
        return 0
    return overlap_max - overlap_min + 1


def _append_negative_band(
    bands: list[RegionSplitBand],
    rows: list[int],
    row_dark_pixels: dict[int, list[tuple[int, int]]],
    min_band_height: int,
) -> None:
    if len(rows) < min_band_height:
        return
    pixels = [pixel for y in rows for pixel in row_dark_pixels[y]]
    if not pixels:
        return
    xs = [x for x, _ in pixels]
    ys = [y for _, y in pixels]
    bands.append(
        RegionSplitBand(
            band_id=len(bands),
            component_ids=(),
            bounding_box=BoundingBox(
                min_x=min(xs),
                min_y=min(ys),
                max_x=max(xs),
                max_y=max(ys),
            ),
            area=len(pixels),
            x_min=min(xs),
            x_max=max(xs),
            y_min=min(ys),
            y_max=max(ys),
        )
    )
