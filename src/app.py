from __future__ import annotations

from src.config import get_config
from src.logging_setup import configure_logging
from src.safe_paths import ensure_directory


def initialize_application() -> dict[str, str]:
    config = get_config()

    ensure_directory(config.datasets_dir)
    ensure_directory(config.reports_dir)
    ensure_directory(config.docs_dir)
    ensure_directory(config.logs_dir)

    logger = configure_logging(config.logs_dir)
    logger.info("DMD Mask Optimizer foundation initialized")

    return {
        "project_root": str(config.project_root),
        "datasets_dir": str(config.datasets_dir),
        "reports_dir": str(config.reports_dir),
        "docs_dir": str(config.docs_dir),
        "logs_dir": str(config.logs_dir),
        "dmd_dimensions": f"{config.dmd_width}x{config.dmd_height}",
        "valid_pixel_states": ",".join(str(state) for state in config.valid_pixel_states),
    }


def main() -> int:
    summary = initialize_application()
    print("DMD Mask Optimizer foundation is ready.")
    for key, value in summary.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

