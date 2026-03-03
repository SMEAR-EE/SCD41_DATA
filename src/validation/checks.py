"""Validation check functions for per-sensor directory structure.

Directory structure expected:
    output/sensors/{sensor}/csv/     - CSV files
    output/sensors/{sensor}/parquet/ - Parquet files
    output/merged/csv/               - Merged CSVs
    output/merged/parquet/           - Merged parquets

Each check function returns a list of CheckResult objects.
"""

from pathlib import Path
import re
import hashlib
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq
import numpy as np

from .models import CheckResult, SensorSummary, Severity


def discover_year_months(cfg) -> list[tuple[str, str]]:
    """
    Discover all year-month combinations from existing files.
    
    Scans all per-sensor directories for monthly files (both CSV and Parquet)
    and extracts unique year-month combinations from filenames.
    
    Args:
        cfg: PipelineConfig object containing sensors_dir path
    
    Returns:
        Sorted list of (year, month) tuples with years and months as strings,
        e.g., [('2024', '09'), ('2024', '10')]
    """
    year_months = set()
    pattern = re.compile(r'_(\d{4})_(\d{2})\.(?:parquet|csv)$')
    
    # Scan each sensor's directories
    sensors_dir = Path(cfg.sensors_dir)
    if sensors_dir.exists():
        for sensor_dir in sensors_dir.iterdir():
            if not sensor_dir.is_dir():
                continue
            
            # Check parquet directory
            parquet_dir = sensor_dir / 'parquet'
            if parquet_dir.exists():
                for f in parquet_dir.glob("*.parquet"):
                    match = pattern.search(f.name)
                    if match:
                        year_months.add((match.group(1), match.group(2)))
            
            # Check CSV directory
            csv_dir = sensor_dir / 'csv'
            if csv_dir.exists():
                for f in csv_dir.glob("*_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"):
                    match = pattern.search(f.name)
                    if match:
                        year_months.add((match.group(1), match.group(2)))
    
    return sorted(year_months)


def check_column_names(cfg) -> list[CheckResult]:
    """
    Verify no lambda artifacts in column names across all sensors.
    
    Checks all sensor 10min CSV files for column names containing '<lambda>',
    which indicates a pandas aggregation bug where anonymous functions were
    used without proper naming.
    
    Args:
        cfg: PipelineConfig object containing sensors_dir path
    
    Returns:
        List of CheckResult objects, one per sensor CSV file checked
        
    Raises:
        None (errors are captured in CheckResult objects)
    """
    results = []
    sensors_dir = Path(cfg.sensors_dir)
    
    if not sensors_dir.exists():
        return [CheckResult(
            name="column_names",
            passed=False,
            message=f"Sensors directory not found: {sensors_dir}",
            severity=Severity.CRITICAL
        )]
    
    # Check each sensor's 10min CSV
    for sensor_dir in sorted(sensors_dir.iterdir()):
        if not sensor_dir.is_dir():
            continue
        
        csv_dir = sensor_dir / 'csv'
        if not csv_dir.exists():
            continue
        
        for csv_file in sorted(csv_dir.glob("*_10min.csv")):
            try:
                df = pd.read_csv(csv_file, nrows=1)
                bad_cols = [c for c in df.columns if '<lambda>' in c]
                
                passed = len(bad_cols) == 0
                result = CheckResult(
                    name=f"column_names:{sensor_dir.name}/{csv_file.name}",
                    passed=passed,
                    message="Clean" if passed else f"Lambda artifacts: {bad_cols}",
                    details={"bad_columns": bad_cols},
                    severity=Severity.CRITICAL
                )
            except Exception as e:
                result = CheckResult(
                    name=f"column_names:{sensor_dir.name}/{csv_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)},
                    severity=Severity.CRITICAL
                )
            
            results.append(result)
    
    return results


def check_file_inventory(cfg, sensor_names: list[str]) -> tuple[list[CheckResult], dict[str, SensorSummary]]:
    """
    Inventory all CSV and parquet files per sensor.
    
    For each sensor, counts monthly CSV and Parquet files, verifies they match,
    and computes statistics including total rows, date range, and data coverage.
    
    Args:
        cfg: PipelineConfig object containing directory paths
        sensor_names: List of sensor names to check (e.g., ['CO2_SCT1_2M', 'LGR_30M'])
    
    Returns:
        Tuple of (check_results, sensor_summaries):
            - check_results: List of CheckResult objects for CSV/Parquet match validation
            - sensor_summaries: Dict mapping sensor names to SensorSummary objects
            
    Raises:
        None (errors are captured in CheckResult objects)
    """
    results = []
    summaries = {}
    
    for sensor in sensor_names:
        # Get per-sensor directories
        sensor_dirs = cfg.get_sensor_dirs(sensor)
        csv_dir = sensor_dirs['csv']
        parquet_dir = sensor_dirs['parquet']
        
        # Find monthly CSVs
        monthly_csvs = sorted(csv_dir.glob(f"{sensor}_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv")) if csv_dir.exists() else []
        months_csv = [f.stem.split('_')[-2] + '-' + f.stem.split('_')[-1] for f in monthly_csvs]
        
        # Find parquet files
        monthly_pqs = sorted(parquet_dir.glob(f"{sensor}_[0-9][0-9][0-9][0-9]_[0-9][0-9].parquet")) if parquet_dir.exists() else []
        months_pq = [f.stem.split('_')[-2] + '-' + f.stem.split('_')[-1] for f in monthly_pqs]
        
        # Check for combined files
        combined_csv = csv_dir / f"{sensor}_10min.csv"
        combined_pq = parquet_dir / f"{sensor}_10min.parquet"
        has_combined_csv = combined_csv.exists()
        has_combined_pq = combined_pq.exists()

        # Calculate stats from parquets
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
        
        # Calculate coverage
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
        summaries[sensor] = summary
        
        # Check result
        csv_pq_match = set(months_csv) == set(months_pq)
        results.append(CheckResult(
            name=f"file_inventory:{sensor}",
            # passed=csv_pq_match and len(months_pq) > 0,
            passed=csv_pq_match and len(months_pq) > 0 and has_combined_csv,
            message=f"{len(months_csv)} CSVs, {len(months_pq)} parquets" + 
                    ("" if csv_pq_match else " [MISMATCH]"),
            details={
                "csv_months": months_csv,
                "parquet_months": months_pq,
                "csv_parquet_match": csv_pq_match,
                "csv_dir": str(csv_dir),
                "parquet_dir": str(parquet_dir)
            },
            severity=Severity.CRITICAL
        ))
    
    return results, summaries


def check_parquet_integrity(cfg) -> list[CheckResult]:
    """
    Validate parquet file integrity, schema, and compression across all sensors.
    
    Checks each Parquet file for:
    - Presence of 'timestamp' column
    - Correct datetime dtype for timestamp
    - Compression format (expects SNAPPY)
    - Empty/all-NaN columns
    - File readability
    
    Args:
        cfg: PipelineConfig object containing sensors_dir path
    
    Returns:
        List of CheckResult objects, one per Parquet file checked
        
    Raises:
        None (errors are captured in CheckResult objects)
    """
    results = []
    sensors_dir = Path(cfg.sensors_dir)
    
    if not sensors_dir.exists():
        return [CheckResult(
            name="parquet_integrity",
            passed=False,
            message=f"Sensors directory not found: {sensors_dir}",
            severity=Severity.CRITICAL
        )]
    
    # Check each sensor's parquet directory
    for sensor_dir in sorted(sensors_dir.iterdir()):
        if not sensor_dir.is_dir():
            continue
        
        parquet_dir = sensor_dir / 'parquet'
        if not parquet_dir.exists():
            continue
        
        for pq_file in sorted(parquet_dir.glob("*.parquet")):
            try:
                pq_meta = pq.read_metadata(pq_file)
                df = pd.read_parquet(pq_file)
                
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
                    name=f"parquet:{sensor_dir.name}/{pq_file.name}",
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
                    severity=Severity.CRITICAL if not has_ts else Severity.WARNING if nan_cols else Severity.CRITICAL
                )
            except Exception as e:
                result = CheckResult(
                    name=f"parquet:{sensor_dir.name}/{pq_file.name}",
                    passed=False,
                    message=f"Read error: {e}",
                    details={"error": str(e)},
                    severity=Severity.CRITICAL
                )
            
            results.append(result)
    
    return results


def check_csv_parquet_consistency(
    cfg, 
    year_months: list[tuple[str, str]]
) -> list[CheckResult]:
    """
    Verify CSV and parquet files contain identical data.
    
    Compares monthly CSV and Parquet files for key sensors to ensure:
    - Row counts match
    - Numeric values match (within floating-point tolerance)
    
    Only checks representative sensors (CO2_SCT1_2M, LGR_30M) to avoid
    redundant validation across all sensors.
    
    Args:
        cfg: PipelineConfig object containing directory paths
        year_months: List of (year, month) tuples to check, e.g., [('2024', '09')]
    
    Returns:
        List of CheckResult objects for each sensor-month combination checked
        
    Raises:
        None (errors are captured in CheckResult objects)
    """
    results = []
    
    # Check key sensors only
    # check_sensors = ["CO2_SCT1_2M", "LGR_30M"]
    check_sensors = ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"]
    
    for sensor in check_sensors:
        sensor_dirs = cfg.get_sensor_dirs(sensor)
        csv_dir = sensor_dirs['csv']
        parquet_dir = sensor_dirs['parquet']
        
        for year, month in year_months:
            csv_path = csv_dir / f"{sensor}_{year}_{month}.csv"
            pq_path = parquet_dir / f"{sensor}_{year}_{month}.parquet"
            
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
    
    return results


def check_merged_data(cfg) -> tuple[CheckResult, dict]:
    """
    Validate the merged dataset.
    
    Checks the main merged CSV file (SMEAR_EE_CO2_merged.csv) for:
    - File existence and readability
    - Total rows and columns
    - Date range coverage
    - Consistency with monthly Parquet files
    - Column coverage statistics for key sensors
    
    Args:
        cfg: PipelineConfig object containing merged_dir path
    
    Returns:
        Tuple of (check_result, merged_summary):
            - check_result: CheckResult object for merged data validation
            - merged_summary: Dict with statistics (rows, columns, date_range, coverage, etc.)
            
    Raises:
        None (errors are captured in CheckResult)
    """
    merged_dirs = cfg.get_merged_dirs()
    merged_csv = merged_dirs['csv'] / "SMEAR_EE_CO2_merged.csv"
    merged_summary = {}
    
    if not merged_csv.exists():
        return CheckResult(
            name="merged_data",
            passed=False,
            message="Merged file not found",
            details={"expected_path": str(merged_csv)},
            severity=Severity.CRITICAL
        ), merged_summary
    
    try:
        df = pd.read_csv(merged_csv, parse_dates=['timestamp'])
        
        merged_summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "date_range": {
                "start": str(df['timestamp'].min()),
                "end": str(df['timestamp'].max())
            },
            "file_size_mb": round(merged_csv.stat().st_size / (1024 * 1024), 2)
        }
        
        # Check monthly parquets
        merged_pq_dir = merged_dirs['parquet']
        if merged_pq_dir.exists():
            monthly_pqs = sorted(merged_pq_dir.glob("*.parquet"))
            if monthly_pqs:
                total_pq_rows = sum(len(pd.read_parquet(p)) for p in monthly_pqs)
                merged_summary["monthly_parquet_sum_match"] = total_pq_rows == len(df)
                merged_summary["monthly_parquet_total_rows"] = total_pq_rows
       
        # Check combined merged parquet
        merged_pq_combined = merged_pq_dir / "SMEAR_EE_CO2_merged.parquet"
        if merged_pq_combined.exists():
            pq_df = pd.read_parquet(merged_pq_combined)
            merged_summary["combined_parquet_rows"] = len(pq_df)
            merged_summary["combined_parquet_match"] = len(pq_df) == len(df)
        else:
            merged_summary["combined_parquet_exists"] = False
       
        # Column coverage
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
        merged_summary["column_coverage"] = coverage
        
        result = CheckResult(
            name="merged_data",
            passed=True,
            message=f"{len(df):,} rows, {len(df.columns)} columns, {merged_summary['file_size_mb']:.1f} MB | {merged_summary['date_range']['start'][:10]} to {merged_summary['date_range']['end'][:10]}",
            details=merged_summary,
            severity=Severity.CRITICAL
        )
        
    except Exception as e:
        result = CheckResult(
            name="merged_data",
            passed=False,
            message=f"Error: {e}",
            details={"error": str(e)},
            severity=Severity.CRITICAL
        )
    
    return result, merged_summary


def compute_quality_metrics(cfg) -> tuple[CheckResult, dict]:
    """
    Compute data quality metrics including sensor comparison.
    
    Analyzes the merged dataset to compute:
    - Time continuity (gaps > 10 minutes)
    - Sensor validation statistics (bias, RMSE, correlation, MAE)
    - Comparison of SCD41 sensors against LGR reference
    
    Validation metrics computed:
    - n_valid_pairs: Number of timestamps with data from both sensors
    - bias_ppm: Mean difference (sensor - reference)
    - rmse_ppm: Root mean squared error
    - correlation: Pearson correlation coefficient
    - mae_ppm: Mean absolute error
    
    Args:
        cfg: PipelineConfig object containing merged_dir path
    
    Returns:
        Tuple of (check_result, quality_metrics):
            - check_result: CheckResult object summarizing quality
            - quality_metrics: Dict with detailed statistics for each sensor comparison
            
    Raises:
        None (errors are captured in CheckResult)
    """
    merged_dirs = cfg.get_merged_dirs()
    merged_csv = merged_dirs['csv'] / "SMEAR_EE_CO2_merged.csv"
    quality_metrics = {}
    
    if not merged_csv.exists():
        return CheckResult(
            name="data_quality",
            passed=False,
            message="Merged file not found",
            severity=Severity.WARNING
        ), quality_metrics
    
    try:
        df = pd.read_csv(merged_csv, parse_dates=['timestamp'])
        df = df.sort_values('timestamp')
        
        # Time continuity
        time_diffs = df['timestamp'].diff()
        gaps = time_diffs[time_diffs > pd.Timedelta(minutes=10)]
        
        quality_metrics["time_continuity"] = {
            "gaps_over_10min": len(gaps),
            "largest_gap": str(gaps.max()) if len(gaps) > 0 else "N/A"
        }
        
        # SCD41 2m vs LGR comparison
        lgr_col = 'lgr_30m_CO2_dry_mean'
        scd_col = 'co2_sct1_2m_co2_mean'
        
        if lgr_col in df.columns and scd_col in df.columns:
            valid = df[lgr_col].notna() & df[scd_col].notna()
            
            if valid.sum() > 0:
                diff = df[scd_col][valid] - df[lgr_col][valid]
                quality_metrics["scd41_2m_vs_lgr"] = {
                    "n_valid_pairs": int(valid.sum()),
                    "bias_ppm": round(diff.mean(), 1),
                    "rmse_ppm": round(np.sqrt((diff**2).mean()), 1),
                    "correlation": round(df[scd_col][valid].corr(df[lgr_col][valid]), 3),
                    "mae_ppm": round(diff.abs().mean(), 1),
                    "std_ppm": round(diff.std(), 1)
                }
        
        # 30m sensor comparisons
        for sensor_col in ['co2_30m_a_co2_mean', 'co2_30m_b_co2_mean', 'co2_30m_c_co2_mean']:
            if lgr_col in df.columns and sensor_col in df.columns:
                valid = df[lgr_col].notna() & df[sensor_col].notna()
                
                if valid.sum() > 100:
                    diff = df[sensor_col][valid] - df[lgr_col][valid]
                    sensor_name = sensor_col.replace('_co2_mean', '').upper()
                    quality_metrics[f"{sensor_name}_vs_lgr"] = {
                        "n_valid_pairs": int(valid.sum()),
                        "bias_ppm": round(diff.mean(), 1),
                        "rmse_ppm": round(np.sqrt((diff**2).mean()), 1),
                        "correlation": round(df[sensor_col][valid].corr(df[lgr_col][valid]), 3),
                        "std_ppm": round(diff.std(), 1)
                    }
        
        bias = quality_metrics.get('scd41_2m_vs_lgr', {}).get('bias_ppm', 'N/A')
        result = CheckResult(
            name="data_quality",
            passed=True,
            message=f"{len(gaps)} time gaps >10min, bias={bias} ppm",
            details=quality_metrics,
            severity=Severity.INFO
        )
        
    except Exception as e:
        result = CheckResult(
            name="data_quality",
            passed=False,
            message=f"Error: {e}",
            details={"error": str(e)},
            severity=Severity.WARNING
        )
    
    return result, quality_metrics


def compute_checksums(cfg, include_all: bool = False) -> dict[str, str]:
    """
    Compute SHA256 checksums for key output files.
    
    Generates cryptographic checksums for data integrity verification and
    reproducibility tracking. Always computes checksum for merged CSV.
    Optionally includes all sensor Parquet files.
    
    Args:
        cfg: PipelineConfig object containing directory paths
        include_all: If True, compute checksums for all sensor Parquet files
                     (default: False, only merged CSV)
    
    Returns:
        Dict mapping file paths to SHA256 hex digest strings
        Example: {'SMEAR_EE_CO2_merged.csv': 'abc123...', ...}
        
    Raises:
        IOError: If files cannot be read (not caught internally)
    """
    checksums = {}
    
    def sha256(filepath: Path) -> str:
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    
    merged_dirs = cfg.get_merged_dirs()
    
    # Merged CSV
    merged_csv = merged_dirs['csv'] / "SMEAR_EE_CO2_merged.csv"
    if merged_csv.exists():
        checksums[merged_csv.name] = sha256(merged_csv)
    
    # Optionally all sensor parquets
    if include_all:
        sensors_dir = Path(cfg.sensors_dir)
        for sensor_dir in sorted(sensors_dir.iterdir()):
            if not sensor_dir.is_dir():
                continue
            parquet_dir = sensor_dir / 'parquet'
            if parquet_dir.exists():
                for pq_file in sorted(parquet_dir.glob("*.parquet")):
                    checksums[f"{sensor_dir.name}/{pq_file.name}"] = sha256(pq_file)
    
    return checksums


def check_verification(cfg) -> list[CheckResult]:
    """
    Run verification checks on processed data.
    
    Performs comprehensive data integrity checks on each sensor's main CSV file:
    - Timestamp parsing validity (no unparseable timestamps)
    - No duplicate timestamps (data corruption check)
    - Timestamp continuity (gaps > 10 minutes are logged but expected)
    - No all-NaN data columns
    
    Note: Time gaps are expected in real-world sensor data due to downtime,
    so they generate warnings rather than critical failures.
    
    Args:
        cfg: PipelineConfig object containing sensors_dir path
    
    Returns:
        List of CheckResult objects, one per sensor checked. Each result
        includes details about rows, invalid timestamps, duplicates, gaps,
        and empty columns.
        
    Raises:
        None (errors are captured in CheckResult objects)
    """
    results = []
    sensors_dir = Path(cfg.sensors_dir)
    
    if not sensors_dir.exists():
        return results
    
    for sensor_dir in sorted(sensors_dir.iterdir()):
        if not sensor_dir.is_dir():
            continue
        
        csv_dir = sensor_dir / 'csv'
        main_csv = csv_dir / f"{sensor_dir.name}_10min.csv"
        
        if not main_csv.exists():
            continue
        
        try:
            df = pd.read_csv(main_csv)
            
            # Robust timestamp parsing (same as other functions)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
            
            # Check for unparseable timestamps
            invalid_ts = df['timestamp'].isna().sum()
            
            issues = []
            
            if invalid_ts > 0:
                issues.append(f"{invalid_ts} invalid timestamps")
            
            # Check for duplicate timestamps
            dup_count = df['timestamp'].duplicated().sum()
            if dup_count > 0:
                issues.append(f"{dup_count} duplicate timestamps")
            
            # Check timestamp continuity (gaps > 10 min)
            large_gaps = 0
            if len(df) > 1 and invalid_ts < len(df):
                df_sorted = df.dropna(subset=['timestamp']).sort_values('timestamp')
                if len(df_sorted) > 1:
                    gaps = df_sorted['timestamp'].diff()
                    large_gaps = (gaps > pd.Timedelta(minutes=10)).sum()
                    if large_gaps > 0:
                        issues.append(f"{large_gaps} gaps >10min")
            
            # Check for all-NaN data columns (excluding timestamp, qc columns)
            data_cols = [c for c in df.columns if c != 'timestamp' and not c.endswith('_qc')]
            all_nan_cols = [c for c in data_cols if df[c].isna().all()]
            if all_nan_cols:
                issues.append(f"{len(all_nan_cols)} empty columns")
            
            # Determine severity: gaps are expected, but duplicates/invalid timestamps are problems
            has_critical = dup_count > 0 or invalid_ts > 0 or len(all_nan_cols) > 0
            
            passed = len(issues) == 0
            result = CheckResult(
                name=f"verification:{sensor_dir.name}",
                passed=passed,
                message="OK" if passed else "; ".join(issues),
                details={
                    "rows": len(df),
                    "invalid_timestamps": int(invalid_ts),
                    "duplicate_timestamps": int(dup_count),
                    "gaps_over_10min": int(large_gaps),
                    "empty_columns": all_nan_cols
                },
                severity=Severity.CRITICAL if has_critical else Severity.WARNING
            )
        except Exception as e:
            result = CheckResult(
                name=f"verification:{sensor_dir.name}",
                passed=False,
                message=f"Error: {e}",
                details={"error": str(e)},
                severity=Severity.CRITICAL
            )
        
        results.append(result)
    
    return results