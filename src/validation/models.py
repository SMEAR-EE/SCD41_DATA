"""Data models for validation module."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Check severity levels."""
    CRITICAL = "critical"  # Data integrity issue - must fix
    WARNING = "warning"    # Potential issue - should investigate
    INFO = "info"          # Informational only


@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)
    severity: Severity = Severity.CRITICAL
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
            "severity": self.severity.value
        }


@dataclass 
class SensorSummary:
    """Summary statistics for a single sensor."""
    name: str
    total_rows: int
    date_range: tuple[str, str]
    coverage_pct: float
    monthly_files: list[str]
    parquet_files: list[str]
    column_count: int
    file_sizes_kb: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "total_rows": self.total_rows,
            "date_range": list(self.date_range),
            "coverage_pct": round(self.coverage_pct, 2),
            "monthly_csv_count": len(self.monthly_files),
            "parquet_count": len(self.parquet_files),
            "column_count": self.column_count,
            "file_sizes_kb": self.file_sizes_kb
        }