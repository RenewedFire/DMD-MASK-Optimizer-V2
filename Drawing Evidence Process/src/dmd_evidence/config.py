from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvidenceConfig:
    project_root: Path
    data_dir: Path
    database_path: Path


def get_config() -> EvidenceConfig:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    return EvidenceConfig(
        project_root=project_root,
        data_dir=data_dir,
        database_path=data_dir / "region_evidence.sqlite",
    )
