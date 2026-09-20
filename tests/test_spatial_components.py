from __future__ import annotations

import unittest

from src.spatial import components_to_payload, find_lit_components


class SpatialComponentTests(unittest.TestCase):
    def test_finds_single_component_with_geometry(self) -> None:
        matrix = (
            (0, 0, 0, 0),
            (0, 1, 1, 0),
            (0, 0, 1, 0),
            (0, 0, 0, 0),
        )

        components = find_lit_components(matrix)

        self.assertEqual(len(components), 1)
        component = components[0]
        self.assertEqual(component.component_id, 0)
        self.assertEqual(component.area, 3)
        self.assertEqual(component.pixels, ((1, 1), (2, 1), (2, 2)))
        self.assertEqual(component.bounding_box.min_x, 1)
        self.assertEqual(component.bounding_box.min_y, 1)
        self.assertEqual(component.bounding_box.max_x, 2)
        self.assertEqual(component.bounding_box.max_y, 2)
        self.assertEqual(component.bounding_box.width, 2)
        self.assertEqual(component.bounding_box.height, 2)
        self.assertAlmostEqual(component.centroid_x, 5 / 3)
        self.assertAlmostEqual(component.centroid_y, 4 / 3)

    def test_diagonal_pixels_are_one_component(self) -> None:
        matrix = (
            (1, 0),
            (0, 1),
        )

        components = find_lit_components(matrix)

        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].pixels, ((0, 0), (1, 1)))
        self.assertEqual(components[0].area, 2)

    def test_edge_connected_pixels_are_one_component(self) -> None:
        matrix = (
            (1, 1, 0),
            (0, 1, 0),
            (0, 1, 1),
        )

        components = find_lit_components(matrix)

        self.assertEqual(len(components), 1)
        self.assertEqual(components[0].area, 5)

    def test_empty_frame_has_no_components(self) -> None:
        matrix = (
            (0, 0, 0),
            (0, 0, 0),
        )

        self.assertEqual(find_lit_components(matrix), ())

    def test_rejects_non_rectangular_matrix(self) -> None:
        matrix = (
            (0, 1, 0),
            (1, 0),
        )

        with self.assertRaisesRegex(ValueError, "rectangular"):
            find_lit_components(matrix)

    def test_payload_contains_review_geometry(self) -> None:
        matrix = (
            (1, 1),
            (0, 0),
        )

        payload = components_to_payload(find_lit_components(matrix))

        self.assertEqual(payload[0]["component_id"], 0)
        self.assertEqual(payload[0]["area"], 2)
        self.assertEqual(payload[0]["bounding_box"]["width"], 2)
        self.assertEqual(payload[0]["bounding_box"]["height"], 1)
        self.assertEqual(payload[0]["pixels"], [{"x": 0, "y": 0}, {"x": 1, "y": 0}])


if __name__ == "__main__":
    unittest.main()
