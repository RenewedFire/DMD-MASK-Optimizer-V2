from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class AppConfig:
    """Stage 0 application configuration."""

    project_root: Path = PROJECT_ROOT
    datasets_dir: Path = PROJECT_ROOT / "datasets"
    reports_dir: Path = PROJECT_ROOT / "reports"
    docs_dir: Path = PROJECT_ROOT / "docs"
    logs_dir: Path = PROJECT_ROOT / "reports" / "logs"
    dmd_width: int = 128
    dmd_height: int = 32
    valid_pixel_states: tuple[int, ...] = (0, 1, 2, 3)


def get_config() -> AppConfig:
    return AppConfig()

