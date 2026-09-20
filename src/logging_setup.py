from __future__ import annotations

import logging
from pathlib import Path

from src.safe_paths import ensure_directory


def configure_logging(logs_dir: Path, level: int = logging.INFO) -> logging.Logger:
    ensure_directory(logs_dir)
    log_path = logs_dir / "dmd_mask_optimizer.log"

    logger = logging.getLogger("dmd_mask_optimizer")
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
