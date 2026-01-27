"""
SMEAR Estonia CO2 Data Validation Module.

Usage
-----
    from src.validation import validate_outputs
    
    # Run validation with default config (config/sensors.yaml)
    validate_outputs()
    
    # Or with custom config path
    validate_outputs("path/to/sensors.yaml")
    
    # Access results
    report = validate_outputs()
    report.checks           # List of CheckResult objects
    report.sensor_summaries # Dict of SensorSummary objects
    report.quality_metrics  # Quality comparison metrics
"""

from pathlib import Path

from .models import Severity, CheckResult, SensorSummary
from .report import ValidationReport
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config/sensors.yaml"


def validate_outputs(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    export_json: bool = True,
    export_markdown: bool = True,
    verbose: bool = True
) -> ValidationReport:
    """
    Run validation and export reports.
    
    Parameters
    ----------
    config_path : str or Path
        Path to sensors.yaml config file. Default: config/sensors.yaml
    export_json : bool
        Export JSON report to <validation_dir>/validation_report.json
    export_markdown : bool
        Export Markdown report to <validation_dir>/VALIDATION_RECEIPT.md
    verbose : bool
        Print summary to console
    
    (Note: validation_dir is configurable via sensors.yaml config file)
    
    Returns
    -------
    ValidationReport
        Completed validation report object
    
    Examples
    --------
    >>> from src.validation import validate_outputs
    >>> validate_outputs()  # Uses config/sensors.yaml
    """
    report = ValidationReport(config_path)
    report.run_all()

    if verbose:
        report.print_summary()
    
    if export_json:
        report.export_json()
        json_path = report.cfg.validation_dir / "validation_report.json"
        report.export_json(json_path)
        logger.info("  JSON report: %s", json_path)
    
    if export_markdown:
        report.export_markdown()
        md_path = report.cfg.validation_dir / "VALIDATION_RECEIPT.md"
        report.export_markdown(md_path)
        logger.info("  Markdown receipt: %s", md_path)
    
    return report


__all__ = [
    "validate_outputs",
    "ValidationReport",
    "CheckResult",
    "SensorSummary",
    "Severity",
]