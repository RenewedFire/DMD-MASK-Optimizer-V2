from __future__ import annotations

import unittest

from src.spatial import (
    component_relationship,
    find_component_relationships,
    find_lit_components,
    relationships_to_payload,
)


class SpatialRelationshipTests(unittest.TestCase):
    def test_horizontal_gap_and_y_overlap(self) -> None:
        components = find_lit_components(
            (
                (1, 1, 0, 0, 1),
                (1, 1, 0, 0, 1),
            )
        )

        relationship = component_relationship(components[0], components[1])

        self.assertEqual(relationship.horizontal_gap, 2)
        self.assertEqual(relationship.vertical_gap, 0)
        self.assertEqual(relationship.x_overlap, 0)
        self.assertEqual(relationship.y_overlap, 2)
        self.assertEqual(relationship.y_overlap_ratio, 1)
        self.assertTrue(relationship.horizontal_adjacent)
        self.assertFalse(relationship.vertical_adjacent)
        self.assertFalse(relationship.touches)

    def test_vertical_gap_and_x_overlap(self) -> None:
        components = find_lit_components(
            (
                (1, 1),
                (0, 0),
                (0, 0),
                (1, 1),
            )
        )

        relationship = component_relationship(components[0], components[1])

        self.assertEqual(relationship.horizontal_gap, 0)
        self.assertEqual(relationship.vertical_gap, 2)
        self.assertEqual(relationship.x_overlap, 2)
        self.assertEqual(relationship.x_overlap_ratio, 1)
        self.assertTrue(relationship.vertical_adjacent)
        self.assertFalse(relationship.horizontal_adjacent)

    def test_diagonal_touching_boxes_touch(self) -> None:
        components = find_lit_components(
            (
                (1, 0, 0),
                (0, 0, 0),
                (0, 0, 1),
            )
        )

        relationship = component_relationship(components[0], components[1])

        self.assertEqual(relationship.horizontal_gap, 1)
        self.assertEqual(relationship.vertical_gap, 1)
        self.assertFalse(relationship.touches)
        self.assertAlmostEqual(relationship.edge_distance, 2**0.5)

    def test_ratio_and_alignment_evidence(self) -> None:
        components = find_lit_components(
            (
                (1, 1, 0, 0, 1, 1),
                (1, 1, 0, 0, 1, 0),
                (0, 0, 0, 0, 1, 0),
            )
        )

        relationship = component_relationship(components[0], components[1])

        self.assertEqual(relationship.area_ratio, 1)
        self.assertEqual(relationship.width_ratio, 1)
        self.assertEqual(relationship.height_ratio, 2 / 3)
        self.assertEqual(relationship.top_delta, 0)
        self.assertEqual(relationship.bottom_delta, 1)

    def test_find_component_relationships_returns_unique_pairs(self) -> None:
        components = find_lit_components(((1, 0, 1, 0, 1),))

        relationships = find_component_relationships(components)

        self.assertEqual(len(relationships), 3)
        self.assertEqual(
            [(item.component_a_id, item.component_b_id) for item in relationships],
            [(0, 1), (0, 2), (1, 2)],
        )

    def test_relationship_payload_is_inspectable(self) -> None:
        components = find_lit_components(((1, 0, 1),))
        payload = relationships_to_payload(find_component_relationships(components))

        self.assertEqual(payload[0]["component_a_id"], 0)
        self.assertEqual(payload[0]["component_b_id"], 1)
        self.assertIn("horizontal_gap", payload[0])
        self.assertIn("centroid_distance", payload[0])
        self.assertIn("x_overlap_ratio", payload[0])


if __name__ == "__main__":
    unittest.main()
