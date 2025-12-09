# src/logging_utils.py
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Path,
    log_name: str = "processing",
    level: int = logging.INFO,
    reset_handlers: bool = True,
    to_stdout: bool = True,
) -> Path:
    """
    Configure application-wide logging.

    Args:
        log_dir: Directory where log files are stored.
        log_name: Base name for the log file (timestamp is appended).
        level: Logging level (e.g., logging.INFO).
        reset_handlers: If True, remove existing handlers first
                        (important for Jupyter to avoid duplicates).
        to_stdout: If True, also log to stdout (StreamHandler).

    Returns:
        Path to the created log file.
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped log file
    log_file = log_dir / f"{log_name}_{datetime.now():%Y%m%d_%H%M%S}.log"

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if reset_handlers:
        for h in list(root_logger.handlers):
            root_logger.removeHandler(h)

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # Optional stdout handler
    if to_stdout:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        root_logger.addHandler(sh)

    root_logger.info(f"Logging initialized. Log file: {log_file}")
    return log_file