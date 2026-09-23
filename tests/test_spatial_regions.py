from __future__ import annotations

import unittest

from src.config import get_config
from src.parsing import parse_dump_file
from src.spatial import (
    discover_spatial_regions,
    find_region_split_evidence,
    find_component_relationships,
    find_lit_components,
    generate_candidate_boxes,
    refine_spatial_regions,
    refined_regions_to_payload,
    region_split_evidence_to_payload,
    regions_to_payload,
)


class SpatialRegionTests(unittest.TestCase):
    def test_candidate_chain_becomes_one_region(self) -> None:
        components = find_lit_components(((1, 0, 1, 0, 1),))
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))

        regions = discover_spatial_regions(components, candidates)

        self.assertEqual(len(regions), 1)
        self.assertEqual(regions[0].component_ids, (0, 1, 2))
        self.assertEqual(regions[0].component_count, 3)
        self.assertEqual(regions[0].bounding_box.min_x, 0)
        self.assertEqual(regions[0].bounding_box.max_x, 4)
        self.assertEqual(regions[0].evidence_pairs, ((0, 1), (1, 2)))

    def test_unconnected_components_remain_singleton_regions(self) -> None:
        components = find_lit_components(((1, 0, 0, 0, 1),))
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(1, 2))

        regions = discover_spatial_regions(components, candidates)

        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0].component_ids, (0,))
        self.assertEqual(regions[1].component_ids, (1,))

    def test_region_payload_is_inspectable(self) -> None:
        components = find_lit_components(((1, 0, 1),))
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))
        regions = discover_spatial_regions(components, candidates)

        payload = regions_to_payload(regions)

        self.assertEqual(payload[0]["region_id"], 0)
        self.assertEqual(payload[0]["component_ids"], [0, 1])
        self.assertEqual(payload[0]["component_count"], 2)
        self.assertEqual(payload[0]["area"], 2)
        self.assertEqual(payload[0]["bounding_box"]["width"], 3)
        self.assertEqual(payload[0]["candidate_ids"], [0])
        self.assertEqual(payload[0]["evidence_pairs"], [{"component_a_id": 0, "component_b_id": 1}])

    def test_horizontal_corridor_creates_split_evidence(self) -> None:
        components = find_lit_components(
            (
                (1, 1, 0, 1, 1),
                (1, 1, 0, 1, 1),
                (0, 0, 0, 0, 0),
                (1, 1, 0, 1, 1),
                (1, 1, 0, 1, 1),
            )
        )
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(3,))
        regions = discover_spatial_regions(components, candidates)

        split_evidence = find_region_split_evidence(components, regions, min_band_height=1)

        self.assertEqual(len(split_evidence), 1)
        self.assertEqual(split_evidence[0].region_id, 0)
        self.assertEqual(split_evidence[0].axis, "horizontal")
        self.assertEqual(split_evidence[0].corridor_rows, (2,))
        self.assertEqual(split_evidence[0].band_count, 2)

    def test_split_evidence_payload_is_inspectable(self) -> None:
        components = find_lit_components(
            (
                (1, 1),
                (0, 0),
                (1, 1),
            )
        )
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(2,))
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(components, regions, min_band_height=1)

        payload = region_split_evidence_to_payload(split_evidence)

        self.assertEqual(payload[0]["split_id"], 0)
        self.assertEqual(payload[0]["region_id"], 0)
        self.assertEqual(payload[0]["axis"], "horizontal")
        self.assertEqual(payload[0]["corridor_rows"], [1])
        self.assertEqual(payload[0]["band_count"], 2)
        self.assertEqual(payload[0]["bands"][0]["component_ids"], [0])

    def test_negative_space_band_creates_split_evidence(self) -> None:
        binary_pixels = (
            (1, 1, 1, 1, 1, 1),
            (1, 0, 0, 0, 0, 1),
            (1, 0, 1, 1, 0, 1),
            (1, 1, 1, 1, 1, 1),
        )
        components = find_lit_components(binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)

        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=binary_pixels,
            min_negative_space_ratio=0.2,
        )

        self.assertTrue(any(split.reason == "negative-space horizontal band" for split in split_evidence))

    def test_mixed_01_bill_paxton_frame_has_lower_band_split_evidence(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[403]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)

        split_evidence = find_region_split_evidence(components, regions)

        self.assertTrue(split_evidence)
        self.assertIn(23, split_evidence[0].corridor_rows)
        self.assertTrue(any(band.y_min >= 24 for band in split_evidence[0].bands))

    def test_mixed_01_negative_space_frame_has_negative_space_evidence(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[500]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)

        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        negative_splits = [
            split for split in split_evidence if split.reason == "negative-space horizontal band"
        ]
        self.assertTrue(negative_splits)
        self.assertTrue(any(len(split.bands) >= 2 for split in negative_splits))

    def test_sample_dump_frame_has_vertical_split_evidence(self) -> None:
        dataset = get_config().datasets_dir / "sample_dump.txt"
        if not dataset.exists():
            self.skipTest("sample_dump.txt is not available")
        frame = parse_dump_file(dataset)[0]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)

        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        vertical_splits = [split for split in split_evidence if split.axis == "vertical"]
        self.assertTrue(vertical_splits)
        self.assertTrue(any(split.band_count >= 3 for split in vertical_splits))

    def test_refinement_uses_horizontal_split_bands(self) -> None:
        components = find_lit_components(
            (
                (1, 1, 0, 1, 1),
                (1, 1, 0, 1, 1),
                (0, 0, 0, 0, 0),
                (1, 1, 0, 1, 1),
                (1, 1, 0, 1, 1),
            )
        )
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(3,))
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(components, regions)

        refined = refine_spatial_regions(regions, split_evidence)

        self.assertEqual(len(refined), 2)
        self.assertEqual(refined[0].source_region_id, 0)
        self.assertEqual(refined[0].source_split_id, 0)
        self.assertEqual(refined[0].refinement_reason, "internal low-occupancy row corridor")

    def test_refined_region_payload_is_inspectable(self) -> None:
        components = find_lit_components(((1, 0, 1),))
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))
        regions = discover_spatial_regions(components, candidates)
        refined = refine_spatial_regions(regions, ())

        payload = refined_regions_to_payload(refined)

        self.assertEqual(payload[0]["refined_region_id"], 0)
        self.assertEqual(payload[0]["source_region_id"], 0)
        self.assertIsNone(payload[0]["source_split_id"])
        self.assertEqual(payload[0]["refinement_reason"], "kept first-pass region")

    def test_insert_coin_frame_refines_text_rows_without_semantics(self) -> None:
        dataset = get_config().datasets_dir / "Insert Coin.txt"
        if not dataset.exists():
            self.skipTest("Insert Coin.txt is not available")
        frame = parse_dump_file(dataset)[10]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        refined = refine_spatial_regions(regions, split_evidence)

        self.assertEqual(len(regions), 2)
        self.assertEqual(len(refined), 3)
        self.assertTrue(any(region.source_split_id is not None for region in refined))

    def test_negative_space_frame_refines_to_two_dark_bands(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[500]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        refined = refine_spatial_regions(regions, split_evidence)

        self.assertEqual(len(refined), 2)
        self.assertEqual(
            {region.refinement_reason for region in refined},
            {"negative-space horizontal band"},
        )

    def test_coherent_large_object_is_not_sliced_into_horizontal_bands(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[850]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        refined = refine_spatial_regions(regions, split_evidence)

        left_object_regions = [
            region
            for region in refined
            if region.bounding_box.min_x < 10 and region.bounding_box.width > 50
        ]
        self.assertEqual(len(left_object_regions), 1)
        self.assertEqual(left_object_regions[0].refinement_reason, "kept first-pass region")

    def test_frame_850_right_region_keeps_horizontal_row_refinement(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[850]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        refined = refine_spatial_regions(regions, split_evidence)

        right_row_regions = [
            region
            for region in refined
            if region.bounding_box.min_x >= 70
            and region.refinement_reason == "internal low-occupancy row corridor"
        ]
        self.assertEqual(len(right_row_regions), 4)

    def test_short_status_band_can_promote_vertical_split_evidence(self) -> None:
        dataset = get_config().datasets_dir / "mixed_01.txt"
        if not dataset.exists():
            self.skipTest("mixed_01.txt is not available")
        frame = parse_dump_file(dataset)[900]
        components = find_lit_components(frame.binary_pixels)
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships)
        regions = discover_spatial_regions(components, candidates)
        split_evidence = find_region_split_evidence(
            components,
            regions,
            binary_pixels=frame.binary_pixels,
        )

        refined = refine_spatial_regions(regions, split_evidence)

        self.assertTrue(
            any(region.refinement_reason.startswith("vertical corridor") for region in refined)
        )
        self.assertGreaterEqual(len(refined), 4)


if __name__ == "__main__":
    unittest.main()
