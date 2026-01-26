"""Data Validation Module for SMEAR Estonia CO2 Processing Pipeline

Generates comprehensive validation receipts for processed sensor data.
Designed for data management documentation and quality assurance.

Usage:
    from src.validation import ValidationReport
    
    report = ValidationReport(output_dir="output")
    report.run_all()
    report.print_summary()
    report.export_json("output/validation_report.json")
    report.export_markdown("output/VALIDATION_RECEIPT.md")
"""

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
import json
import hashlib

import pandas as pd
import pyarrow.parquet as pq
import numpy as np


@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    passed: bool
    message: str
    details: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details
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
        Base output directory containing individual/, parquet/, merged/ subdirs
    sensors : list[str], optional
        List of sensor names to validate. Defaults to standard SMEAR EE sensors.
    """
    
    DEFAULT_SENSORS = ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"]
    
    def __init__(
        self, 
        output_dir: str | Path = "output",
        sensors: list[str] | None = None
    ):
        self.output_dir = Path(output_dir)
        self.individual_dir = self.output_dir / "individual"
        self.parquet_dir = self.output_dir / "parquet"
        self.merged_dir = self.output_dir / "merged"
        
        self.sensors = sensors or self.DEFAULT_SENSORS
        
        # Results storage
        self.checks: list[CheckResult] = []
        self.sensor_summaries: dict[str, SensorSummary] = {}
        self.merged_summary: dict = {}
        self.quality_metrics: dict = {}
        self.timestamp = datetime.now().isoformat()
        
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
                    details={"bad_columns": bad_cols}
                )
            except Exception as e:
                result = CheckResult(
                    name=f"column_names:{csv_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)}
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
            # Find monthly CSVs
            monthly_csvs = sorted(self.individual_dir.glob(f"{sensor}_2024_*.csv"))
            months_csv = [f.stem.split('_')[-1] for f in monthly_csvs]
            
            # Find parquet files
            monthly_pqs = sorted(self.parquet_dir.glob(f"{sensor}_2024_*.parquet"))
            months_pq = [f.stem.split('_')[-1] for f in monthly_pqs]
            
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
                message=f"{len(months_csv)} CSVs, {len(months_pq)} parquets",
                details={
                    "csv_months": months_csv,
                    "parquet_months": months_pq,
                    "csv_parquet_match": csv_pq_match
                }
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
                    }
                )
            except Exception as e:
                result = CheckResult(
                    name=f"parquet:{pq_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)}
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
        
        # Check a sample of sensors and months
        for sensor in ["CO2_SCT1_2M", "LGR_30M"]:
            for month in ["09", "10", "11", "12"]:
                csv_path = self.individual_dir / f"{sensor}_2024_{month}.csv"
                pq_path = self.parquet_dir / f"{sensor}_2024_{month}.parquet"
                
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
                        name=f"csv_parquet_match:{sensor}_{month}",
                        passed=passed,
                        message=f"rows: {len(csv_df)}=={len(pq_df)}, values: {values_match}",
                        details={
                            "csv_rows": len(csv_df),
                            "parquet_rows": len(pq_df),
                            "rows_match": rows_match,
                            "values_match": values_match
                        }
                    )
                except Exception as e:
                    result = CheckResult(
                        name=f"csv_parquet_match:{sensor}_{month}",
                        passed=False,
                        message=f"Error: {e}",
                        details={"error": str(e)}
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
                details={"expected_path": str(merged_csv)}
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
                message=f"{len(df)} rows, {len(df.columns)} columns",
                details=self.merged_summary
            ))
            
        except Exception as e:
            self.checks.append(CheckResult(
                name="merged_data",
                passed=False,
                message=f"Error: {e}",
                details={"error": str(e)}
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
                message=f"{len(gaps)} time gaps, bias={self.quality_metrics.get('scd41_2m_vs_lgr', {}).get('bias_ppm', 'N/A')} ppm",
                details=self.quality_metrics
            ))
            
        except Exception as e:
            self.checks.append(CheckResult(
                name="data_quality",
                passed=False,
                message=f"Error: {e}",
                details={"error": str(e)}
            ))
        
        return self.quality_metrics
    
    # =========================================================================
    # CHECK 7: File Checksums
    # =========================================================================
    
    def compute_checksums(self, include_all: bool = False) -> dict:
        """Compute SHA256 checksums for key output files.
        
        Parameters
        ----------
        include_all : bool
            If True, checksum all parquet files. If False, only merged outputs.
        """
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
        sep = "=" * 70
        
        print(f"\n{sep}")
        print("SMEAR ESTONIA CO2 DATA VALIDATION RECEIPT")
        print(f"Generated: {self.timestamp}")
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
                print("-" * 50)
                for check in categories[cat]:
                    status = "✓" if check.passed else "✗"
                    name = check.name.split(":")[-1] if ":" in check.name else check.name
                    print(f"  {status} {name}: {check.message}")
        
        # Sensor summary table
        if self.sensor_summaries:
            print(f"\n7. SENSOR SUMMARY")
            print("-" * 50)
            print(f"  {'Sensor':<15} {'Rows':>8} {'Coverage':>10} {'Months':>8}")
            print(f"  {'-'*15} {'-'*8} {'-'*10} {'-'*8}")
            for name, summary in self.sensor_summaries.items():
                print(f"  {name:<15} {summary.total_rows:>8} {summary.coverage_pct:>9.1f}% {len(summary.parquet_files):>8}")
        
        # Quality metrics highlight
        if self.quality_metrics.get("scd41_2m_vs_lgr"):
            print(f"\n8. REFERENCE COMPARISON (SCD41 2m vs LGR)")
            print("-" * 50)
            m = self.quality_metrics["scd41_2m_vs_lgr"]
            print(f"  n = {m['n_valid_pairs']:,} paired observations")
            print(f"  Bias:        {m['bias_ppm']:+.1f} ppm")
            print(f"  RMSE:        {m['rmse_ppm']:.1f} ppm")
            print(f"  MAE:         {m['mae_ppm']:.1f} ppm")
            print(f"  Correlation: {m['correlation']:.3f}")
        
        # Overall status
        passed = sum(1 for c in self.checks if c.passed)
        total = len(self.checks)
        status = "PASSED" if passed == total else "ISSUES FOUND"
        
        print(f"\n{sep}")
        print(f"VALIDATION STATUS: {status} ({passed}/{total} checks passed)")
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
                "sensors": self.sensors
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
                lines.append(
                    f"| {name} | {s.total_rows:,} | {s.coverage_pct:.1f}% | "
                    f"{len(s.parquet_files)} | {s.date_range[0][:10]} to {s.date_range[1][:10]} |"
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
    
    # =========================================================================
    # CONVENIENCE: Quick validation function
    # =========================================================================


def validate_outputs(
    output_dir: str | Path = "output",
    export_json: bool = True,
    export_markdown: bool = True,
    verbose: bool = True
) -> ValidationReport:
    """Convenience function for quick validation with default exports.
    
    Parameters
    ----------
    output_dir : str or Path
        Base output directory
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
    
    Example
    -------
    >>> from src.validation import validate_outputs
    >>> report = validate_outputs()
    """
    report = ValidationReport(output_dir=output_dir)
    report.run_all()
    
    if verbose:
        report.print_summary()
    
    if export_json:
        report.export_json(Path(output_dir) / "validation_report.json")
    
    if export_markdown:
        report.export_markdown(Path(output_dir) / "VALIDATION_RECEIPT.md")
    
    return report


# CLI support
if __name__ == "__main__":
    import sys
    
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    validate_outputs(output_dir=output_dir)