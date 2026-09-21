from __future__ import annotations

import unittest

from src.spatial import (
    discover_spatial_regions,
    find_component_relationships,
    find_lit_components,
    generate_candidate_boxes,
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


if __name__ == "__main__":
    unittest.main()
