"""ValidationReport orchestrator class."""

from datetime import datetime
from pathlib import Path
import yaml

from .models import CheckResult, SensorSummary, Severity
from . import checks

# Import from main config module
from src.config import PipelineConfig


class ValidationReport:
    """Orchestrates validation checks and collects results.
    
    Parameters
    ----------
    config_path : str or Path
        Path to sensors.yaml config file.
    
    Examples
    --------
    >>> report = ValidationReport("config/sensors.yaml")
    >>> report.run_all()
    >>> report.print_summary()
    """
    
    def __init__(self, config_path: str | Path = "config/sensors.yaml"):
        config_path = Path(config_path)
        
        # Load pipeline config (handles sensors_dir, merged_dir, sensors)
        self.cfg = PipelineConfig.from_yaml(config_path)
        
        # Get merged directory from config
        self.merged_dir = self.cfg.merged_dir
        
        # Extract sensor names
        self.sensor_names = [s.name for s in self.cfg.sensors]
        self.timestamp = datetime.now().isoformat()
   
        self.verification_checks: list[CheckResult] = []

        # Discover available data
        self.year_months = checks.discover_year_months(self.cfg)
        
        # Results storage
        self.checks: list[CheckResult] = []
        self.sensor_summaries: dict[str, SensorSummary] = {}
        self.merged_summary: dict = {}
        self.quality_metrics: dict = {}
        self.checksums: dict[str, str] = {}
    
    def run_all(self) -> "ValidationReport":
        """Run all validation checks. Returns self for chaining."""
        # 1. Column names
        self.checks.extend(checks.check_column_names(self.cfg))
        
        # 2. File inventory
        inv_results, self.sensor_summaries = checks.check_file_inventory(
            self.cfg, self.sensor_names
        )
        self.checks.extend(inv_results)
        
        # 3. Parquet integrity
        self.checks.extend(checks.check_parquet_integrity(self.cfg))
        
        # 4. CSV/Parquet consistency
        self.checks.extend(checks.check_csv_parquet_consistency(
            self.cfg, self.year_months
        ))
        
        # 5. Merged data (pass config, not path)
        merged_result, self.merged_summary = checks.check_merged_data(self.cfg)
        self.checks.append(merged_result)
        
        # 6. Quality metrics (pass config, not path)
        quality_result, self.quality_metrics = checks.compute_quality_metrics(self.cfg)
        self.checks.append(quality_result)
        
        # 7. Checksums (pass config only)
        self.checksums = checks.compute_checksums(self.cfg)
        
        # 8. Verification checks (if implemented)
        if hasattr(checks, 'check_verification'):
            self.verification_checks = checks.check_verification(self.cfg)
            self.checks.extend(self.verification_checks)
        
        return self
    
    def get_status(self) -> tuple[str, str, dict]:
        """
        Determine overall validation status.
        
        Returns
        -------
        status : str
            One of "PASSED", "PASSED_WITH_WARNINGS", "FAILED"
        message : str
            Human-readable status message
        counts : dict
            Check counts by severity
        """
        critical = [c for c in self.checks if c.severity == Severity.CRITICAL]
        warnings = [c for c in self.checks if c.severity == Severity.WARNING]
        
        critical_passed = sum(1 for c in critical if c.passed)
        warning_passed = sum(1 for c in warnings if c.passed)
        total_passed = sum(1 for c in self.checks if c.passed)
        
        counts = {
            "critical_passed": critical_passed,
            "critical_total": len(critical),
            "warning_passed": warning_passed,
            "warning_total": len(warnings),
            "total_passed": total_passed,
            "total": len(self.checks)
        }
        
        if critical_passed == len(critical):
            if warning_passed == len(warnings):
                return "PASSED", "All checks passed", counts
            else:
                return "PASSED_WITH_WARNINGS", f"{len(warnings) - warning_passed} warning(s) to review", counts
        else:
            return "FAILED", f"{len(critical) - critical_passed} critical issue(s) require attention", counts
    
    def to_dict(self) -> dict:
        """Export report as dictionary (for JSON serialisation)."""
        return {
            "meta": {
                "generated": self.timestamp,
                "sensors_dir": str(self.cfg.sensors_dir),
                "merged_dir": str(self.merged_dir),
                "sensors": self.sensor_names,
                "year_month_range": self.year_months
            },
            "checks": [c.to_dict() for c in self.checks],
            "sensor_summaries": {k: v.to_dict() for k, v in self.sensor_summaries.items()},
            "merged_summary": self.merged_summary,
            "quality_metrics": self.quality_metrics,
            "checksums": self.checksums
        }
    
    # Convenience methods delegate to output module
    def print_summary(self, verbose: bool = True) -> None:
        """Print human-readable summary to console."""
        from .output import print_console_summary
        print_console_summary(self, verbose=verbose)
    
    def export_json(self, filepath: str | Path | None = None) -> Path:
        """Export report as JSON."""
        from .output import export_json
        # if filepath is None:
        #     filepath = self.cfg.sensors_dir.parent / "validation_report.json"
        if filepath is None:
            filepath = self.cfg.validation_dir / "validation_report.json"
        return export_json(self, filepath)
    
    def export_markdown(self, filepath: str | Path | None = None) -> Path:
        """Export report as Markdown using Jinja2 template."""
        from .output import export_markdown
        # if filepath is None:
        #     filepath = self.cfg.sensors_dir.parent / "VALIDATION_RECEIPT.md"
        if filepath is None:
            filepath = self.cfg.validation_dir / "VALIDATION_RECEIPT.md"
        return export_markdown(self, filepath)