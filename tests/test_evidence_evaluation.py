from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.evidence import (
    DetectorOptions,
    analyze_failure_patterns,
    evaluate_evidence_export,
    optimize_detector_options,
)


def _export_payload() -> dict[str, object]:
    pixels = [[0 for _x in range(8)] for _y in range(8)]
    for y in range(1, 4):
        for x in range(1, 4):
            pixels[y][x] = 3
    return {
        "format": "dmd-region-evidence-export",
        "format_version": 1,
        "counts": {"dumps": 1, "evidence_frames": 1, "regions": 1},
        "dumps": [
            {
                "id": 1,
                "content_hash": "hash",
                "filename": "fixture.txt",
                "game_name": None,
                "frame_count": 1,
                "evidence_frames": [
                    {
                        "id": 1,
                        "source_frame_index": 0,
                        "frame_hash": "frame-hash",
                        "frame_width": 8,
                        "frame_height": 8,
                        "descriptor": "single block",
                        "frame": {
                            "source_index": 0,
                            "header": "0x00000000",
                            "width": 8,
                            "height": 8,
                            "pixels": pixels,
                        },
                        "regions": [
                            {
                                "x": 1,
                                "y": 1,
                                "width": 3,
                                "height": 3,
                                "display_order": 0,
                            }
                        ],
                    }
                ],
            }
        ],
    }


class EvidenceEvaluationTests(unittest.TestCase):
    def test_evaluate_export_matches_simple_human_region(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            export_path.write_text(json.dumps(_export_payload()), encoding="utf-8")

            report = evaluate_evidence_export(export_path)

            self.assertEqual(report.frame_count, 1)
            self.assertEqual(report.human_region_count, 1)
            self.assertEqual(report.matched_region_count, 1)
            self.assertEqual(report.missed_region_count, 0)
            self.assertEqual(report.extra_region_count, 0)
            self.assertEqual(report.frame_results[0].descriptor, "single block")

    def test_summary_reports_worst_frames(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            payload = _export_payload()
            payload["dumps"][0]["evidence_frames"][0]["regions"] = [
                {"x": 6, "y": 6, "width": 1, "height": 1, "display_order": 0}
            ]
            export_path.write_text(json.dumps(payload), encoding="utf-8")

            summary = evaluate_evidence_export(export_path).summary()

            self.assertEqual(summary["frame_count"], 1)
            self.assertEqual(len(summary["worst_frames"]), 1)
            self.assertEqual(summary["worst_frames"][0]["missed_count"], 1)

    def test_optimizer_returns_reports_ordered_by_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            export_path.write_text(json.dumps(_export_payload()), encoding="utf-8")

            reports = optimize_detector_options(
                export_path,
                option_grid=(
                    DetectorOptions(max_candidate_threshold=2),
                    DetectorOptions(max_candidate_threshold=3),
                ),
            )

            self.assertEqual(len(reports), 2)
            self.assertGreaterEqual(
                reports[0].mean_alignment_score,
                reports[1].mean_alignment_score,
            )

    def test_failure_analysis_buckets_missed_regions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            payload = _export_payload()
            payload["dumps"][0]["evidence_frames"][0]["regions"] = [
                {"x": 6, "y": 6, "width": 1, "height": 1, "display_order": 0}
            ]
            export_path.write_text(json.dumps(payload), encoding="utf-8")

            patterns = analyze_failure_patterns(export_path)

            self.assertEqual(sum(pattern.count for pattern in patterns), 1)
            self.assertEqual(patterns[0].examples[0]["descriptor"], "single block")


if __name__ == "__main__":
    unittest.main()
