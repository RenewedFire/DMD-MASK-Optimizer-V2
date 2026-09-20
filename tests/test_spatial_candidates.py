from __future__ import annotations

import unittest

from src.spatial import (
    candidate_boxes_to_payload,
    find_component_relationships,
    find_lit_components,
    generate_candidate_boxes,
)


class SpatialCandidateTests(unittest.TestCase):
    def test_generates_candidate_for_near_horizontal_components(self) -> None:
        components = find_lit_components(
            (
                (1, 1, 0, 1, 1),
                (1, 1, 0, 1, 1),
            )
        )
        relationships = find_component_relationships(components)

        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].threshold, 1)
        self.assertEqual(candidates[0].component_ids, (0, 1))
        self.assertEqual(candidates[0].component_count, 2)
        self.assertEqual(candidates[0].bounding_box.min_x, 0)
        self.assertEqual(candidates[0].bounding_box.max_x, 4)
        self.assertEqual(candidates[0].bounding_box.height, 2)
        self.assertEqual(candidates[0].evidence_pairs, ((0, 1),))

    def test_thresholds_preserve_alternate_candidates(self) -> None:
        components = find_lit_components(((1, 0, 0, 1),))
        relationships = find_component_relationships(components)

        candidates = generate_candidate_boxes(components, relationships, thresholds=(1, 2))

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].threshold, 2)

    def test_does_not_generate_candidate_for_far_components(self) -> None:
        components = find_lit_components(((1, 0, 0, 0, 1),))
        relationships = find_component_relationships(components)

        candidates = generate_candidate_boxes(components, relationships, thresholds=(1, 2))

        self.assertEqual(candidates, ())

    def test_transitive_near_components_stay_as_pair_candidates(self) -> None:
        components = find_lit_components(((1, 0, 1, 0, 1),))
        relationships = find_component_relationships(components)

        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0].component_ids, (0, 1))
        self.assertEqual(candidates[1].component_ids, (1, 2))

    def test_candidate_payload_is_inspectable(self) -> None:
        components = find_lit_components(((1, 0, 1),))
        relationships = find_component_relationships(components)
        candidates = generate_candidate_boxes(components, relationships, thresholds=(1,))

        payload = candidate_boxes_to_payload(candidates)

        self.assertEqual(payload[0]["candidate_id"], 0)
        self.assertEqual(payload[0]["threshold"], 1)
        self.assertEqual(payload[0]["component_ids"], [0, 1])
        self.assertEqual(payload[0]["component_count"], 2)
        self.assertEqual(payload[0]["bounding_box"]["width"], 3)
        self.assertEqual(payload[0]["evidence_pairs"], [{"component_a_id": 0, "component_b_id": 1}])


if __name__ == "__main__":
    unittest.main()
