from __future__ import annotations

import tempfile
import unittest
import logging
from pathlib import Path

from src.app import initialize_application
from src.config import get_config
from src.logging_setup import configure_logging
from src.safe_paths import UnsafeOutputPathError, ensure_directory, resolve_within


class FoundationTests(unittest.TestCase):
    def test_config_contains_initial_dmd_contract(self) -> None:
        config = get_config()

        self.assertEqual(config.dmd_width, 128)
        self.assertEqual(config.dmd_height, 32)
        self.assertEqual(config.valid_pixel_states, (0, 1, 2, 3))

    def test_safe_path_accepts_nested_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            resolved = resolve_within(base, "nested", "report.txt")

            self.assertEqual(resolved, base.resolve() / "nested" / "report.txt")

    def test_safe_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            with self.assertRaises(UnsafeOutputPathError):
                resolve_within(base, "..", "outside.txt")

    def test_logging_creates_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            logs_dir = Path(tmp) / "logs"

            logger = configure_logging(logs_dir)
            logger.info("test message")

            self.assertTrue((logs_dir / "dmd_mask_optimizer.log").is_file())
            logging.shutdown()

    def test_application_initializes_required_directories(self) -> None:
        summary = initialize_application()

        for key in ("datasets_dir", "reports_dir", "docs_dir", "logs_dir"):
            self.assertTrue(Path(summary[key]).is_dir())


if __name__ == "__main__":
    unittest.main()
