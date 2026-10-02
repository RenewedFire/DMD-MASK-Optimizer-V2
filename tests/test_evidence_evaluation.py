from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from src.evidence import (
    DetectorOptions,
    LayoutPriorOptions,
    analyze_failure_patterns,
    evaluate_evidence_export,
    evaluate_evidence_export_with_layout_prior,
    optimize_layout_prior_options,
    optimize_detector_options,
    train_layout_prior_model,
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

    def test_layout_prior_learns_repeated_logical_region_without_current_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            payload = _export_payload()
            pixels = [[0 for _x in range(10)] for _y in range(10)]
            for y in range(1, 8):
                for x in range(1, 8):
                    pixels[y][x] = 3
            evidence_frame = payload["dumps"][0]["evidence_frames"][0]
            evidence_frame["frame"]["pixels"] = pixels
            evidence_frame["frame"]["width"] = 10
            evidence_frame["frame"]["height"] = 10
            evidence_frame["frame_width"] = 10
            evidence_frame["frame_height"] = 10
            evidence_frame["regions"] = [
                {"x": 0, "y": 0, "width": 10, "height": 10, "display_order": 0}
            ]
            payload["dumps"][0]["evidence_frames"] = [
                {**evidence_frame, "id": index + 1, "source_frame_index": index}
                for index in range(6)
            ]
            export_path.write_text(json.dumps(payload), encoding="utf-8")

            baseline = evaluate_evidence_export(export_path)
            learned = evaluate_evidence_export_with_layout_prior(export_path)
            model = train_layout_prior_model(
                payload,
                exclude_frame_ids=(1,),
                dump_filename="fixture.txt",
            )

            self.assertGreaterEqual(learned.matched_region_count, baseline.matched_region_count)
            self.assertEqual(
                [
                    (
                        template.bounding_box.min_x,
                        template.bounding_box.min_y,
                        template.bounding_box.max_x,
                        template.bounding_box.max_y,
                    )
                    for template in model.templates
                ],
                [(0, 0, 9, 9)],
            )

    def test_layout_prior_optimizer_reuses_baseline_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export_path = Path(tmp) / "evidence.json"
            payload = _export_payload()
            pixels = [[0 for _x in range(10)] for _y in range(10)]
            for y in range(1, 8):
                for x in range(1, 8):
                    pixels[y][x] = 3
            evidence_frame = payload["dumps"][0]["evidence_frames"][0]
            evidence_frame["frame"]["pixels"] = pixels
            evidence_frame["frame"]["width"] = 10
            evidence_frame["frame"]["height"] = 10
            evidence_frame["frame_width"] = 10
            evidence_frame["frame_height"] = 10
            evidence_frame["regions"] = [
                {"x": 0, "y": 0, "width": 10, "height": 10, "display_order": 0}
            ]
            payload["dumps"][0]["evidence_frames"] = [
                {**evidence_frame, "id": index + 1, "source_frame_index": index}
                for index in range(6)
            ]
            export_path.write_text(json.dumps(payload), encoding="utf-8")

            reports = optimize_layout_prior_options(
                export_path,
                (
                    LayoutPriorOptions(),
                    LayoutPriorOptions(min_support_count=99),
                ),
            )

            self.assertGreaterEqual(
                reports[0].matched_region_count,
                reports[1].matched_region_count,
            )


if __name__ == "__main__":
    unittest.main()
