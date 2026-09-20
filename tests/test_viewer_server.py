from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import AppConfig
from viewer import server


WIDTH = 128
HEIGHT = 32
PIXELS_PER_FRAME = WIDTH * HEIGHT


def frame_text(header: str, pixels: str) -> str:
    rows = [pixels[index : index + WIDTH] for index in range(0, len(pixels), WIDTH)]
    return header + "\n" + "\n".join(rows) + "\n\n"


class ViewerServerTests(unittest.TestCase):
    def make_config(self, root: Path) -> AppConfig:
        return AppConfig(
            project_root=root,
            datasets_dir=root / "datasets",
            reports_dir=root / "reports",
            docs_dir=root / "docs",
            logs_dir=root / "reports" / "logs",
        )

    def test_dataset_summary_uses_locked_parser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            datasets = root / "datasets"
            datasets.mkdir()
            pixels = "0123" * (PIXELS_PER_FRAME // 4)
            (datasets / "example.txt").write_text(
                frame_text("0x00000001", pixels), encoding="utf-8"
            )

            with patch("viewer.server.get_config", return_value=self.make_config(root)):
                summary = server.dataset_summary("example.txt")

        self.assertEqual(summary["frame_count"], 1)
        self.assertEqual(summary["width"], WIDTH)
        self.assertEqual(summary["height"], HEIGHT)
        self.assertEqual(summary["first_header"], "0x00000001")

    def test_dataset_frame_returns_exact_and_binary_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            datasets = root / "datasets"
            datasets.mkdir()
            pixels = "0123" * (PIXELS_PER_FRAME // 4)
            (datasets / "example.txt").write_text(
                frame_text("0x00000002", pixels), encoding="utf-8"
            )

            with patch("viewer.server.get_config", return_value=self.make_config(root)):
                payload = server.dataset_frame("example.txt", 0)

        frame = payload["frame"]
        self.assertEqual(frame["header"], "0x00000002")
        self.assertEqual(frame["exact_pixels"][0][:4], (0, 1, 2, 3))
        self.assertEqual(frame["binary_pixels"][0][:4], (0, 1, 1, 1))
        self.assertTrue(len(frame["components"]) > 0)
        self.assertIn("bounding_box", frame["components"][0])
        self.assertIn("relationship_count", frame)
        self.assertIn("relationships", frame)
        self.assertIn("candidate_box_count", frame)
        self.assertIn("candidate_boxes", frame)

    def test_rejects_dataset_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "datasets").mkdir()

            with patch("viewer.server.get_config", return_value=self.make_config(root)):
                with self.assertRaises(FileNotFoundError):
                    server.resolve_dataset("../outside.txt")

    def test_frame_payload_is_json_serializable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            datasets = root / "datasets"
            datasets.mkdir()
            pixels = "3" * PIXELS_PER_FRAME
            (datasets / "example.txt").write_text(
                frame_text("0x00000003", pixels), encoding="utf-8"
            )

            with patch("viewer.server.get_config", return_value=self.make_config(root)):
                payload = server.dataset_frame("example.txt", 0)

        encoded = json.dumps(payload)
        self.assertIn("0x00000003", encoded)


if __name__ == "__main__":
    unittest.main()
