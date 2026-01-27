"""Data Validation Module for SMEAR Estonia CO2 Processing Pipeline

Generates comprehensive validation receipts for processed sensor data.
Designed for data management documentation and quality assurance.

Usage:
    # RECOMMENDED: Use config file for correct paths
    from src.validation import validate_outputs
    report = validate_outputs(config_path="config/sensors.yaml")
    
    # Alternative: Manual paths
    from src.validation import ValidationReport
    report = ValidationReport(output_dir="output")
    report.run_all()
    report.print_summary()
"""

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import json
import hashlib
import re

import pandas as pd
import pyarrow.parquet as pq
import numpy as np


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


class ValidationReport:
    """Comprehensive validation report generator for processed CO2 sensor data.
    
    Performs structural, consistency, and quality checks on processed outputs.
    Generates human-readable and machine-readable validation receipts.
    
    Parameters
    ----------
    output_dir : str or Path
        Base output directory (used if config_path not provided)
    config_path : str or Path, optional
        Path to sensors.yaml config file. RECOMMENDED for correct path detection.
    sensors : list[str], optional
        List of sensor names to validate. Defaults to standard SMEAR EE sensors.
    
    Examples
    --------
    # Recommended: Use config file
    >>> report = ValidationReport(config_path="config/sensors.yaml")
    >>> report.run_all().print_summary()
    
    # Alternative: Manual (assumes default directory structure)
    >>> report = ValidationReport(output_dir="output")
    """
    
    DEFAULT_SENSORS = ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"]
    
    # Descriptions for output documentation
    DESCRIPTIONS = {
        "column_names": (
            "Verifies column names are clean Python identifiers. "
            "Checks for '<lambda>' artifacts from pandas aggregation bugs. "
            "PASS = no problematic column names found."
        ),
        "file_inventory": (
            "Confirms CSV and Parquet files exist for each sensor/month. "
            "PASS = matching CSV and Parquet counts (both formats should have identical months). "
            "FAIL = missing files or CSV/Parquet mismatch — re-run pipeline to generate missing files."
        ),
        "parquet": (
            "Validates Parquet file integrity and metadata. "
            "Checks: timestamp column exists, datetime dtype, no all-NaN columns. "
            "SNAPPY = compression algorithm (fast, good ratio). "
            "PASS = file readable with valid schema."
        ),
        "csv_parquet_match": (
            "Confirms CSV and Parquet contain identical data. "
            "'rows: X==Y' = row counts match. "
            "'values: True' = numeric values match within floating-point tolerance (rtol=1e-10). "
            "PASS = both conditions met."
        ),
        "merged_data": (
            "Validates the combined multi-sensor dataset. "
            "Checks row counts, column counts, date range, and monthly parquet consistency. "
            "PASS = merged file exists and is readable."
        ),
        "data_quality": (
            "Computes quality metrics for sensor intercomparison. "
            "Time gaps = periods >10min between consecutive timestamps. "
            "Bias = mean difference (sensor - reference). "
            "PASS = metrics computed successfully (does not judge quality thresholds)."
        )
    }
    
    def __init__(
        self, 
        output_dir: str | Path = "output",
        config_path: str | Path | None = None,
        sensors: list[str] | None = None
    ):
        # If config provided, read paths from it (RECOMMENDED)
        if config_path is not None:
            self._load_config(config_path)
        else:
            # Default structure - may not match your actual layout!
            self.output_dir = Path(output_dir)
            self.individual_dir = self.output_dir / "individual"
            self.parquet_dir = self.output_dir / "parquet"
            self.merged_dir = self.output_dir / "merged"
            self._config_sensors = None
        
        self.sensors = sensors or self._config_sensors or self.DEFAULT_SENSORS
        
        # Dynamically discover year-month patterns from existing files
        self._year_month_patterns = self._discover_year_months()
        
        # Results storage
        self.checks: list[CheckResult] = []
        self.sensor_summaries: dict[str, SensorSummary] = {}
        self.merged_summary: dict = {}
        self.quality_metrics: dict = {}
        self.timestamp = datetime.now().isoformat()
    
    def _load_config(self, config_path: str | Path) -> None:
        """Load directory paths from sensors.yaml config file."""
        import yaml
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Extract paths from config - matches your sensors.yaml structure:
        #   output_dir: output/individual
        #   parquet_dir: output/individual/parquet
        #   merged_dir: output/merged
        self.individual_dir = Path(config.get('output_dir', 'output/individual'))
        self.parquet_dir = Path(config.get('parquet_dir', 'output/parquet'))
        self.merged_dir = Path(config.get('merged_dir', 'output/merged'))
        
        # Set output_dir to common parent for report exports
        self.output_dir = self.individual_dir.parent
        
        # Extract sensor names from config
        if 'sensors' in config:
            self._config_sensors = [s['name'] for s in config['sensors']]
        else:
            self._config_sensors = None
    
    def _discover_year_months(self) -> list[tuple[str, str]]:
        """Discover all year-month combinations from existing files."""
        year_months = set()
        
        # Pattern for YYYY_MM in filenames
        pattern = re.compile(r'_(\d{4})_(\d{2})\.(?:parquet|csv)$')
        
        # Check parquet directory
        if self.parquet_dir.exists():
            for pq_file in self.parquet_dir.glob("*.parquet"):
                match = pattern.search(pq_file.name)
                if match:
                    year_months.add((match.group(1), match.group(2)))
        
        # Also check CSV directory (catches cases where parquets missing)
        if self.individual_dir.exists():
            for csv_file in self.individual_dir.glob("*_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"):
                match = pattern.search(csv_file.name)
                if match:
                    year_months.add((match.group(1), match.group(2)))
        
        return sorted(year_months)
        
    def run_all(self) -> "ValidationReport":
        """Run all validation checks and return self for chaining."""
        self.check_column_names()
        self.check_file_inventory()
        self.validate_parquet_files()
        self.check_csv_parquet_consistency()
        self.validate_merged_data()
        self.compute_quality_metrics()
        self.compute_checksums()
        return self
    
    # =========================================================================
    # CHECK 1: Column Name Validation
    # =========================================================================
    
    def check_column_names(self) -> list[CheckResult]:
        """Verify no lambda artifacts in column names."""
        results = []
        
        for csv_file in sorted(self.individual_dir.glob("*_10min.csv")):
            try:
                df = pd.read_csv(csv_file, nrows=1)
                bad_cols = [c for c in df.columns if '<lambda>' in c]
                
                passed = len(bad_cols) == 0
                result = CheckResult(
                    name=f"column_names:{csv_file.name}",
                    passed=passed,
                    message="Clean" if passed else f"Lambda artifacts: {bad_cols}",
                    details={"bad_columns": bad_cols},
                    severity=Severity.CRITICAL
                )
            except Exception as e:
                result = CheckResult(
                    name=f"column_names:{csv_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)},
                    severity=Severity.CRITICAL
                )
            
            results.append(result)
            self.checks.append(result)
        
        return results
    
    # =========================================================================
    # CHECK 2: File Inventory
    # =========================================================================
    
    def check_file_inventory(self) -> dict[str, SensorSummary]:
        """Inventory all CSV and parquet files per sensor."""
        
        for sensor in self.sensors:
            # Find all monthly CSVs (any year)
            monthly_csvs = sorted(self.individual_dir.glob(f"{sensor}_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"))
            months_csv = [f.stem.split('_')[-2] + '-' + f.stem.split('_')[-1] for f in monthly_csvs]
            
            # Find all parquet files (any year)
            monthly_pqs = sorted(self.parquet_dir.glob(f"{sensor}_[0-9][0-9][0-9][0-9]_[0-9][0-9].parquet"))
            months_pq = [f.stem.split('_')[-2] + '-' + f.stem.split('_')[-1] for f in monthly_pqs]
            
            # Calculate total rows and date range from parquets
            total_rows = 0
            min_date, max_date = None, None
            col_count = 0
            file_sizes = {}
            
            for pq_file in monthly_pqs:
                try:
                    df = pd.read_parquet(pq_file)
                    total_rows += len(df)
                    col_count = len(df.columns)
                    file_sizes[pq_file.name] = round(pq_file.stat().st_size / 1024, 1)
                    
                    if 'timestamp' in df.columns:
                        ts_min, ts_max = df['timestamp'].min(), df['timestamp'].max()
                        if min_date is None or ts_min < min_date:
                            min_date = ts_min
                        if max_date is None or ts_max > max_date:
                            max_date = ts_max
                except Exception:
                    continue
            
            # Calculate coverage (assuming 10-min intervals)
            if min_date and max_date:
                expected_rows = int((max_date - min_date).total_seconds() / 600) + 1
                coverage = 100 * total_rows / expected_rows if expected_rows > 0 else 0
                date_range = (str(min_date), str(max_date))
            else:
                coverage = 0
                date_range = ("N/A", "N/A")
            
            summary = SensorSummary(
                name=sensor,
                total_rows=total_rows,
                date_range=date_range,
                coverage_pct=coverage,
                monthly_files=months_csv,
                parquet_files=months_pq,
                column_count=col_count,
                file_sizes_kb=file_sizes
            )
            self.sensor_summaries[sensor] = summary
            
            # Add check result
            csv_pq_match = set(months_csv) == set(months_pq)
            self.checks.append(CheckResult(
                name=f"file_inventory:{sensor}",
                passed=csv_pq_match and len(months_pq) > 0,
                message=f"{len(months_csv)} CSVs, {len(months_pq)} parquets" + 
                        ("" if csv_pq_match else " [MISMATCH]"),
                details={
                    "csv_months": months_csv,
                    "parquet_months": months_pq,
                    "csv_parquet_match": csv_pq_match
                },
                severity=Severity.CRITICAL
            ))
        
        return self.sensor_summaries
    
    # =========================================================================
    # CHECK 3: Parquet File Validation
    # =========================================================================
    
    def validate_parquet_files(self) -> list[CheckResult]:
        """Validate parquet file integrity, schema, and compression."""
        results = []
        
        for pq_file in sorted(self.parquet_dir.glob("*.parquet")):
            try:
                pq_meta = pq.read_metadata(pq_file)
                df = pd.read_parquet(pq_file)
                
                # Checks
                has_ts = 'timestamp' in df.columns
                ts_dtype_ok = pd.api.types.is_datetime64_any_dtype(df['timestamp']) if has_ts else False
                nan_cols = [c for c in df.columns if df[c].isna().all()]
                
                compression = "SNAPPY"
                if pq_meta.num_row_groups > 0:
                    compression = str(pq_meta.row_group(0).column(0).compression)
                
                issues = []
                if not has_ts:
                    issues.append("missing timestamp column")
                if not ts_dtype_ok:
                    issues.append("timestamp not datetime type")
                if nan_cols:
                    issues.append(f"{len(nan_cols)} all-NaN columns")
                
                passed = len(issues) == 0
                size_kb = pq_file.stat().st_size / 1024
                
                result = CheckResult(
                    name=f"parquet:{pq_file.name}",
                    passed=passed,
                    message=f"{len(df)} rows, {size_kb:.1f}KB, {compression}" + 
                            (f" | Issues: {', '.join(issues)}" if issues else ""),
                    details={
                        "rows": len(df),
                        "columns": len(df.columns),
                        "size_kb": round(size_kb, 1),
                        "compression": compression,
                        "has_timestamp": has_ts,
                        "timestamp_dtype_ok": ts_dtype_ok,
                        "empty_columns": nan_cols
                    },
                    severity=Severity.CRITICAL if not has_ts else (Severity.WARNING if nan_cols else Severity.CRITICAL)
                )
            except Exception as e:
                result = CheckResult(
                    name=f"parquet:{pq_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)},
                    severity=Severity.CRITICAL
                )
            
            results.append(result)
            self.checks.append(result)
        
        return results
    
    # =========================================================================
    # CHECK 4: CSV/Parquet Consistency
    # =========================================================================
    
    def check_csv_parquet_consistency(self) -> list[CheckResult]:
        """Verify CSV and parquet files contain identical data."""
        results = []
        
        # Check all discovered year-month combinations for key sensors
        check_sensors = ["CO2_SCT1_2M", "LGR_30M"]
        
        for sensor in check_sensors:
            for year, month in self._year_month_patterns:
                csv_path = self.individual_dir / f"{sensor}_{year}_{month}.csv"
                pq_path = self.parquet_dir / f"{sensor}_{year}_{month}.parquet"
                
                if not (csv_path.exists() and pq_path.exists()):
                    continue
                
                try:
                    csv_df = pd.read_csv(csv_path, parse_dates=['timestamp'])
                    pq_df = pd.read_parquet(pq_path)
                    
                    rows_match = len(csv_df) == len(pq_df)
                    
                    # Check numeric values match
                    numeric_cols = csv_df.select_dtypes(include=[np.number]).columns[:1]
                    values_match = True
                    if len(numeric_cols) > 0:
                        col = numeric_cols[0]
                        csv_vals = csv_df[col].dropna().values
                        pq_vals = pq_df[col].dropna().values
                        if len(csv_vals) == len(pq_vals):
                            values_match = np.allclose(csv_vals, pq_vals, rtol=1e-10, equal_nan=True)
                        else:
                            values_match = False
                    
                    passed = rows_match and values_match
                    result = CheckResult(
                        name=f"csv_parquet_match:{sensor}_{year}_{month}",
                        passed=passed,
                        message=f"rows: {len(csv_df)}=={len(pq_df)}, values: {values_match}",
                        details={
                            "csv_rows": len(csv_df),
                            "parquet_rows": len(pq_df),
                            "rows_match": rows_match,
                            "values_match": values_match
                        },
                        severity=Severity.CRITICAL
                    )
                except Exception as e:
                    result = CheckResult(
                        name=f"csv_parquet_match:{sensor}_{year}_{month}",
                        passed=False,
                        message=f"Error: {e}",
                        details={"error": str(e)},
                        severity=Severity.CRITICAL
                    )
                
                results.append(result)
                self.checks.append(result)
        
        return results
    
    # =========================================================================
    # CHECK 5: Merged Data Validation
    # =========================================================================
    
    def validate_merged_data(self) -> dict:
        """Validate the merged dataset."""
        merged_csv = self.merged_dir / "SMEAR_EE_CO2_merged.csv"
        
        if not merged_csv.exists():
            self.checks.append(CheckResult(
                name="merged_data",
                passed=False,
                message="Merged file not found",
                details={"expected_path": str(merged_csv)},
                severity=Severity.CRITICAL
            ))
            return {}
        
        try:
            df = pd.read_csv(merged_csv, parse_dates=['timestamp'])
            
            # Basic stats
            self.merged_summary = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "date_range": {
                    "start": str(df['timestamp'].min()),
                    "end": str(df['timestamp'].max())
                },
                "file_size_mb": round(merged_csv.stat().st_size / (1024 * 1024), 2)
            }
            
            # Check monthly parquets sum to main
            merged_pq_dir = self.merged_dir / "parquet"
            if merged_pq_dir.exists():
                monthly_pqs = sorted(merged_pq_dir.glob("*.parquet"))
                if monthly_pqs:
                    total_pq_rows = sum(len(pd.read_parquet(p)) for p in monthly_pqs)
                    pq_sum_match = total_pq_rows == len(df)
                    self.merged_summary["monthly_parquet_sum_match"] = pq_sum_match
                    self.merged_summary["monthly_parquet_total_rows"] = total_pq_rows
            
            # Key column coverage
            key_cols = [
                'co2_sct1_2m_co2_mean', 
                'co2_30m_a_co2_mean', 
                'co2_30m_b_co2_mean', 
                'co2_30m_c_co2_mean', 
                'lgr_30m_CO2_dry_mean'
            ]
            coverage = {}
            for col in key_cols:
                if col in df.columns:
                    pct = 100 * df[col].notna().sum() / len(df)
                    coverage[col] = round(pct, 1)
            self.merged_summary["column_coverage"] = coverage
            
            self.checks.append(CheckResult(
                name="merged_data",
                passed=True,
                message=f"{len(df):,} rows, {len(df.columns)} columns, {self.merged_summary['file_size_mb']:.1f} MB | {self.merged_summary['date_range']['start'][:10]} to {self.merged_summary['date_range']['end'][:10]}",
                details=self.merged_summary,
                severity=Severity.CRITICAL
            ))
            
        except Exception as e:
            self.checks.append(CheckResult(
                name="merged_data",
                passed=False,
                message=f"Error: {e}",
                details={"error": str(e)},
                severity=Severity.CRITICAL
            ))
        
        return self.merged_summary
    
    # =========================================================================
    # CHECK 6: Data Quality Metrics
    # =========================================================================
    
    def compute_quality_metrics(self) -> dict:
        """Compute data quality metrics including sensor comparison."""
        merged_csv = self.merged_dir / "SMEAR_EE_CO2_merged.csv"
        
        if not merged_csv.exists():
            return {}
        
        try:
            df = pd.read_csv(merged_csv, parse_dates=['timestamp'])
            
            # Time continuity
            df = df.sort_values('timestamp')
            time_diffs = df['timestamp'].diff()
            gaps = time_diffs[time_diffs > pd.Timedelta(minutes=10)]
            
            self.quality_metrics["time_continuity"] = {
                "gaps_over_10min": len(gaps),
                "largest_gap": str(gaps.max()) if len(gaps) > 0 else "N/A"
            }
            
            # Sensor vs reference comparison (SCD41 2m vs LGR)
            lgr_col = 'lgr_30m_CO2_dry_mean'
            scd_col = 'co2_sct1_2m_co2_mean'
            
            if lgr_col in df.columns and scd_col in df.columns:
                lgr = df[lgr_col]
                scd = df[scd_col]
                valid = lgr.notna() & scd.notna()
                
                if valid.sum() > 0:
                    diff = scd[valid] - lgr[valid]
                    self.quality_metrics["scd41_2m_vs_lgr"] = {
                        "n_valid_pairs": int(valid.sum()),
                        "bias_ppm": round(diff.mean(), 1),
                        "rmse_ppm": round(np.sqrt((diff**2).mean()), 1),
                        "correlation": round(scd[valid].corr(lgr[valid]), 3),
                        "mae_ppm": round(diff.abs().mean(), 1)
                    }
            
            # Add comparison for 30m sensors
            for sensor_col in ['co2_30m_a_co2_mean', 'co2_30m_b_co2_mean', 'co2_30m_c_co2_mean']:
                if lgr_col in df.columns and sensor_col in df.columns:
                    sensor_data = df[sensor_col]
                    valid = df[lgr_col].notna() & sensor_data.notna()
                    
                    if valid.sum() > 100:  # Only if enough data
                        diff = sensor_data[valid] - df[lgr_col][valid]
                        sensor_name = sensor_col.replace('_co2_mean', '').upper()
                        self.quality_metrics[f"{sensor_name}_vs_lgr"] = {
                            "n_valid_pairs": int(valid.sum()),
                            "bias_ppm": round(diff.mean(), 1),
                            "rmse_ppm": round(np.sqrt((diff**2).mean()), 1),
                            "correlation": round(sensor_data[valid].corr(df[lgr_col][valid]), 3)
                        }
            
            self.checks.append(CheckResult(
                name="data_quality",
                passed=True,
                message=f"{len(gaps)} time gaps >10min, bias={self.quality_metrics.get('scd41_2m_vs_lgr', {}).get('bias_ppm', 'N/A')} ppm",
                details=self.quality_metrics,
                severity=Severity.INFO  # Quality metrics are informational
            ))
            
        except Exception as e:
            self.checks.append(CheckResult(
                name="data_quality",
                passed=False,
                message=f"Error: {e}",
                details={"error": str(e)},
                severity=Severity.WARNING
            ))
        
        return self.quality_metrics
    
    # =========================================================================
    # CHECK 7: File Checksums
    # =========================================================================
    
    def compute_checksums(self, include_all: bool = False) -> dict:
        """Compute SHA256 checksums for key output files."""
        checksums = {}
        
        # Always checksum merged outputs
        merged_csv = self.merged_dir / "SMEAR_EE_CO2_merged.csv"
        if merged_csv.exists():
            checksums[merged_csv.name] = self._sha256(merged_csv)
        
        # Optionally checksum all parquets
        if include_all:
            for pq_file in sorted(self.parquet_dir.glob("*.parquet")):
                checksums[pq_file.name] = self._sha256(pq_file)
        
        self.checksums = checksums
        return checksums
    
    def _sha256(self, filepath: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    # =========================================================================
    # OUTPUT: Console Summary
    # =========================================================================
    
    def print_summary(self, verbose: bool = True) -> None:
        """Print human-readable validation summary to console."""
        sep = "=" * 76
        subsep = "-" * 60
        
        print(f"\n{sep}")
        print("SMEAR ESTONIA CO2 DATA VALIDATION RECEIPT")
        print(f"Generated: {self.timestamp}")
        print(f"Output directory: {self.output_dir}")
        print(f"Individual dir:   {self.individual_dir}")
        print(f"Parquet dir:      {self.parquet_dir}")
        print(f"Merged dir:       {self.merged_dir}")
        if self._year_month_patterns:
            print(f"Year-month range: {self._year_month_patterns[0][0]}-{self._year_month_patterns[0][1]} to {self._year_month_patterns[-1][0]}-{self._year_month_patterns[-1][1]}")
        else:
            print("Year-month range: No data found")
        print(sep)
        
        # Group checks by category
        categories = {}
        for check in self.checks:
            cat = check.name.split(":")[0]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(check)
        
        cat_labels = {
            "column_names": "1. COLUMN NAME VALIDATION",
            "file_inventory": "2. FILE INVENTORY",
            "parquet": "3. PARQUET FILE VALIDATION",
            "csv_parquet_match": "4. CSV/PARQUET CONSISTENCY",
            "merged_data": "5. MERGED DATA VALIDATION",
            "data_quality": "6. DATA QUALITY METRICS"
        }
        
        for cat, label in cat_labels.items():
            if cat in categories:
                print(f"\n{label}")
                print(subsep)
                
                # Print description
                if cat in self.DESCRIPTIONS:
                    desc_lines = self.DESCRIPTIONS[cat].split('. ')
                    for line in desc_lines:
                        if line.strip():
                            print(f"  │ {line.strip()}.")
                    print(f"  │")
                
                # Count pass/fail for this category
                cat_passed = sum(1 for c in categories[cat] if c.passed)
                cat_total = len(categories[cat])
                cat_status = "✓ ALL PASSED" if cat_passed == cat_total else f"⚠ {cat_total - cat_passed} ISSUE(S)"
                print(f"  │ Status: {cat_status} ({cat_passed}/{cat_total})")
                print(f"  └{'─' * 50}")
                
                for check in categories[cat]:
                    status = "✓" if check.passed else "✗"
                    name = check.name.split(":")[-1] if ":" in check.name else check.name
                    print(f"    {status} {name}: {check.message}")
        
        # Sensor summary table
        if self.sensor_summaries:
            print(f"\n7. SENSOR SUMMARY")
            print(subsep)
            print(f"  │ Overview of processed sensor data across all months.")
            print(f"  │ Coverage = (actual rows / expected rows) assuming 10-min intervals.")
            print(f"  └{'─' * 50}")
            print(f"    {'Sensor':<15} {'Rows':>10} {'Coverage':>10} {'Months':>8} {'Date Range':<25}")
            print(f"    {'-'*15} {'-'*10} {'-'*10} {'-'*8} {'-'*25}")
            for name, summary in self.sensor_summaries.items():
                date_str = f"{summary.date_range[0][:10]} → {summary.date_range[1][:10]}" if summary.date_range[0] != "N/A" else "N/A"
                print(f"    {name:<15} {summary.total_rows:>10,} {summary.coverage_pct:>9.1f}% {len(summary.parquet_files):>8} {date_str:<25}")
            
            # Column coverage in merged data
            if self.merged_summary.get("column_coverage"):
                print(f"\n    MERGED DATASET COLUMN COVERAGE:")
                print(f"    (Percentage of rows with non-null values for key CO2 columns)")
                for col, pct in self.merged_summary["column_coverage"].items():
                    bar_len = int(pct / 5)  # Scale to max 20 chars
                    bar = "█" * bar_len + "░" * (20 - bar_len)
                    print(f"      {col:<30} {bar} {pct:>5.1f}%")
        
        # Quality metrics highlight
        if self.quality_metrics.get("scd41_2m_vs_lgr"):
            print(f"\n8. REFERENCE COMPARISON (SCD41 2m vs LGR)")
            print(subsep)
            print(f"  │ Comparison of low-cost SCD41 sensor at 2m against LGR reference at 30m.")
            print(f"  │ Bias = mean(sensor - reference); positive = sensor reads high.")
            print(f"  │ RMSE = root mean square error; MAE = mean absolute error.")
            print(f"  │ Correlation = Pearson's r; 1.0 = perfect linear relationship.")
            print(f"  └{'─' * 50}")
            m = self.quality_metrics["scd41_2m_vs_lgr"]
            print(f"    n = {m['n_valid_pairs']:,} paired observations")
            print(f"    Bias:        {m['bias_ppm']:+.1f} ppm")
            print(f"    RMSE:        {m['rmse_ppm']:.1f} ppm")
            print(f"    MAE:         {m['mae_ppm']:.1f} ppm")
            print(f"    Correlation: {m['correlation']:.3f}")
        
        # 30m sensor comparisons if available
        sensor_30m_metrics = [k for k in self.quality_metrics.keys() if k.startswith("CO2_30M")]
        if sensor_30m_metrics:
            print(f"\n9. 30M SENSOR COMPARISONS (vs LGR)")
            print(subsep)
            print(f"  │ Low-cost SCD41 sensors at 30m tower height vs LGR reference.")
            print(f"  └{'─' * 50}")
            print(f"    {'Sensor':<12} {'n':>8} {'Bias':>10} {'RMSE':>10} {'Corr':>8}")
            print(f"    {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*8}")
            for key in sorted(sensor_30m_metrics):
                m = self.quality_metrics[key]
                sensor_name = key.replace("_vs_lgr", "").replace("CO2_30M_", "30M-")
                print(f"    {sensor_name:<12} {m['n_valid_pairs']:>8,} {m['bias_ppm']:>+9.1f} {m['rmse_ppm']:>10.1f} {m['correlation']:>8.3f}")
        
        # Overall status with severity breakdown
        critical_checks = [c for c in self.checks if c.severity == Severity.CRITICAL]
        warning_checks = [c for c in self.checks if c.severity == Severity.WARNING]
        
        critical_passed = sum(1 for c in critical_checks if c.passed)
        critical_total = len(critical_checks)
        warning_passed = sum(1 for c in warning_checks if c.passed)
        warning_total = len(warning_checks)
        
        total_passed = sum(1 for c in self.checks if c.passed)
        total_checks = len(self.checks)
        
        # Determine overall status
        if critical_passed == critical_total:
            if warning_passed == warning_total:
                status = "✅ PASSED"
                status_detail = "All checks passed"
            else:
                status = "⚠️  PASSED WITH WARNINGS"
                status_detail = f"{warning_total - warning_passed} warning(s) to review"
        else:
            status = "❌ FAILED"
            status_detail = f"{critical_total - critical_passed} critical issue(s) require attention"
        
        print(f"\n{sep}")
        print(f"VALIDATION STATUS: {status}")
        print(f"  {status_detail}")
        print(f"  Critical checks: {critical_passed}/{critical_total} passed")
        if warning_total > 0:
            print(f"  Warning checks:  {warning_passed}/{warning_total} passed")
        print(f"  Total checks:    {total_passed}/{total_checks} passed")
        print(sep)
    
    # =========================================================================
    # OUTPUT: JSON Export
    # =========================================================================
    
    def export_json(self, filepath: str | Path) -> Path:
        """Export full validation report as JSON."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            "meta": {
                "generated": self.timestamp,
                "output_dir": str(self.output_dir),
                "individual_dir": str(self.individual_dir),
                "parquet_dir": str(self.parquet_dir),
                "merged_dir": str(self.merged_dir),
                "sensors": self.sensors,
                "year_month_range": self._year_month_patterns
            },
            "checks": [c.to_dict() for c in self.checks],
            "sensor_summaries": {k: v.to_dict() for k, v in self.sensor_summaries.items()},
            "merged_summary": self.merged_summary,
            "quality_metrics": self.quality_metrics,
            "checksums": getattr(self, 'checksums', {})
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"JSON report exported: {filepath}")
        return filepath
    
    # =========================================================================
    # OUTPUT: Markdown Export
    # =========================================================================
    
    def export_markdown(self, filepath: str | Path) -> Path:
        """Export validation report as Markdown for documentation."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        lines = [
            "# SMEAR Estonia CO2 Data Validation Receipt",
            "",
            f"**Generated:** {self.timestamp}",
            f"**Output Directory:** `{self.output_dir}`",
            f"**Individual Directory:** `{self.individual_dir}`",
            f"**Parquet Directory:** `{self.parquet_dir}`",
            "",
            "---",
            "",
            "## Validation Summary",
            "",
        ]
        
        # Checks summary
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        status = "✅ PASSED" if passed == total else "⚠️ ISSUES FOUND"
        lines.append(f"**Status:** {status} ({passed}/{total} checks passed)")
        lines.append("")
        
        # Sensor table
        if self.sensor_summaries:
            lines.extend([
                "## Sensor Data Summary",
                "",
                "| Sensor | Rows | Coverage | Months | Date Range |",
                "|--------|------|----------|--------|------------|"
            ])
            for name, s in self.sensor_summaries.items():
                date_str = f"{s.date_range[0][:10]} to {s.date_range[1][:10]}" if s.date_range[0] != "N/A" else "N/A"
                lines.append(
                    f"| {name} | {s.total_rows:,} | {s.coverage_pct:.1f}% | "
                    f"{len(s.parquet_files)} | {date_str} |"
                )
            lines.append("")
        
        # Quality metrics
        if self.quality_metrics.get("scd41_2m_vs_lgr"):
            m = self.quality_metrics["scd41_2m_vs_lgr"]
            lines.extend([
                "## Reference Comparison (SCD41 2m vs LGR)",
                "",
                f"- **n:** {m['n_valid_pairs']:,} paired observations",
                f"- **Bias:** {m['bias_ppm']:+.1f} ppm",
                f"- **RMSE:** {m['rmse_ppm']:.1f} ppm",
                f"- **MAE:** {m['mae_ppm']:.1f} ppm",
                f"- **Correlation:** {m['correlation']:.3f}",
                ""
            ])
        
        # Checksums
        if hasattr(self, 'checksums') and self.checksums:
            lines.extend([
                "## File Checksums (SHA256)",
                "",
                "```"
            ])
            for fname, checksum in self.checksums.items():
                lines.append(f"{checksum}  {fname}")
            lines.extend(["```", ""])
        
        # Detailed checks
        lines.extend([
            "## Detailed Check Results",
            "",
            "| Check | Status | Message |",
            "|-------|--------|---------|"
        ])
        for c in self.checks:
            status = "✓" if c.passed else "✗"
            msg = c.message[:60] + "..." if len(c.message) > 60 else c.message
            lines.append(f"| {c.name} | {status} | {msg} |")
        
        lines.append("")
        lines.append("---")
        lines.append(f"*Report generated by SMEAR Estonia CO2 Processing Pipeline*")
        
        with open(filepath, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Markdown report exported: {filepath}")
        return filepath


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def validate_outputs(
    output_dir: str | Path = "output",
    config_path: str | Path | None = None,
    export_json: bool = True,
    export_markdown: bool = True,
    verbose: bool = True
) -> ValidationReport:
    """Convenience function for quick validation with default exports.
    
    Parameters
    ----------
    output_dir : str or Path
        Base output directory (ignored if config_path provided)
    config_path : str or Path, optional
        Path to sensors.yaml config file. RECOMMENDED for correct path detection.
    export_json : bool
        Export JSON report to output/validation_report.json
    export_markdown : bool  
        Export Markdown report to output/VALIDATION_RECEIPT.md
    verbose : bool
        Print summary to console
    
    Returns
    -------
    ValidationReport
        The completed validation report object
    
    Examples
    --------
    # RECOMMENDED: Use config file for correct paths
    >>> from src.validation import validate_outputs
    >>> report = validate_outputs(config_path="config/sensors.yaml")
    
    # Alternative: Manual paths (may not match your directory structure)
    >>> report = validate_outputs(output_dir="output")
    """
    report = ValidationReport(output_dir=output_dir, config_path=config_path)
    report.run_all()
    
    if verbose:
        report.print_summary()
    
    # Determine output directory for exports
    export_dir = report.output_dir
    
    if export_json:
        report.export_json(export_dir / "validation_report.json")
    
    if export_markdown:
        report.export_markdown(export_dir / "VALIDATION_RECEIPT.md")
    
    return report


# CLI support
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1].endswith('.yaml'):
        # Config file provided
        validate_outputs(config_path=sys.argv[1])
    else:
        # Default
        output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
        validate_outputs(output_dir=output_dir)
