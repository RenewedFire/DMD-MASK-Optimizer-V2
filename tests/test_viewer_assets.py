from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ViewerAssetTests(unittest.TestCase):
    def read_asset(self, name: str) -> str:
        return (PROJECT_ROOT / "viewer" / name).read_text(encoding="utf-8")

    def test_candidate_review_panel_controls_exist(self) -> None:
        html = self.read_asset("index.html")

        self.assertIn('id="candidateLimitInput"', html)
        self.assertIn('id="candidateComponentInput"', html)
        self.assertIn('id="candidateSummary"', html)
        self.assertIn('id="candidateList"', html)

    def test_candidate_review_logic_is_selectable_and_cumulative(self) -> None:
        script = self.read_asset("viewer.js")

        self.assertIn("selectedCandidate", script)
        self.assertIn("renderCandidateReview", script)
        self.assertIn("selectCandidate", script)
        self.assertIn("candidate.threshold <= Number(state.candidateOverlay)", script)

    def test_component_review_panel_controls_exist(self) -> None:
        html = self.read_asset("index.html")

        self.assertIn('id="componentIdSelect"', html)
        self.assertIn('id="componentLimitInput"', html)
        self.assertIn('id="componentMinAreaInput"', html)
        self.assertIn('id="componentSummary"', html)
        self.assertIn('id="componentList"', html)

    def test_component_review_logic_is_selectable(self) -> None:
        script = self.read_asset("viewer.js")

        self.assertIn("selectedComponentId", script)
        self.assertIn("renderComponentReview", script)
        self.assertIn("selectComponent", script)
        self.assertIn("drawComponentIds", script)

    def test_region_review_panel_controls_exist(self) -> None:
        html = self.read_asset("index.html")

        self.assertIn('id="regionOverlaySelect"', html)
        self.assertIn('id="regionLimitInput"', html)
        self.assertIn('id="regionMinComponentsInput"', html)
        self.assertIn('id="regionStatus"', html)
        self.assertIn('value="1"', html)
        self.assertIn('id="regionSummary"', html)
        self.assertIn('id="regionList"', html)

    def test_region_review_logic_is_selectable(self) -> None:
        script = self.read_asset("viewer.js")

        self.assertIn("selectedRegion", script)
        self.assertIn("renderRegionReview", script)
        self.assertIn("selectRegion", script)
        self.assertIn("drawRegionOverlay", script)


if __name__ == "__main__":
    unittest.main()
