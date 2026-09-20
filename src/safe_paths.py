from __future__ import annotations

from pathlib import Path


class UnsafeOutputPathError(ValueError):
    """Raised when output would escape an approved project directory."""


def resolve_within(base_dir: Path, *parts: str) -> Path:
    base = base_dir.resolve()
    candidate = base.joinpath(*parts).resolve()

    if candidate != base and base not in candidate.parents:
        raise UnsafeOutputPathError(f"Path escapes allowed directory: {candidate}")

    return candidate


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path

