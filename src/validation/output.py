"""Output formatters for validation reports."""

from pathlib import Path
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import Severity


# Descriptions for console output
DESCRIPTIONS = {
    "column_names": (
        "Verifies column names are clean Python identifiers. "
        "Checks for '<lambda>' artifacts from pandas aggregation bugs. "
        "PASS = no problematic column names found."
    ),
    "file_inventory": (
        "Confirms CSV and Parquet files exist for each sensor/month. "
        "PASS = matching CSV and Parquet counts. "
        "FAIL = missing files or CSV/Parquet mismatch."
    ),
    "parquet": (
        "Validates Parquet file integrity and metadata. "
        "SNAPPY = compression algorithm. "
        "PASS = file readable with valid schema."
    ),
    "csv_parquet_match": (
        "Confirms CSV and Parquet contain identical data. "
        "'values: True' = numeric values match within tolerance. "
        "PASS = both row counts and values match."
    ),
    "merged_data": (
        "Validates the combined multi-sensor dataset. "
        "PASS = merged file exists and is readable."
    ),
    "data_quality": (
        "Computes quality metrics for sensor intercomparison. "
        "Time gaps = periods >10min between timestamps. "
        "Bias = mean(sensor - reference)."
    )
}


def print_console_summary(report, verbose: bool = True) -> None:
    """Print human-readable validation summary to console."""
    sep = "=" * 76
    subsep = "-" * 60
    
    cfg = report.cfg
    
    print(f"\n{sep}")
    print("SMEAR ESTONIA CO2 DATA VALIDATION RECEIPT")
    print(f"Generated: {report.timestamp}")
    print(f"Sensors dir:      {cfg.sensors_dir}")
    print(f"Merged dir:       {report.merged_dir}")
    if report.year_months:
        ym_start = f"{report.year_months[0][0]}-{report.year_months[0][1]}"
        ym_end = f"{report.year_months[-1][0]}-{report.year_months[-1][1]}"
        print(f"Year-month range: {ym_start} to {ym_end}")
    else:
        print("Year-month range: No data found")
    print(sep)
    
    # Group checks by category
    categories = {}
    for check in report.checks:
        cat = check.name.split(":")[0]
        categories.setdefault(cat, []).append(check)
    
    cat_labels = {
        "column_names": "1. COLUMN NAME VALIDATION",
        "file_inventory": "2. FILE INVENTORY",
        "parquet": "3. PARQUET FILE VALIDATION",
        "csv_parquet_match": "4. CSV/PARQUET CONSISTENCY",
        "merged_data": "5. MERGED DATA VALIDATION",
        "data_quality": "6. DATA QUALITY METRICS"
    }
    
    for cat, label in cat_labels.items():
        if cat not in categories:
            continue
        
        print(f"\n{label}")
        print(subsep)
        
        # Description
        if cat in DESCRIPTIONS:
            for line in DESCRIPTIONS[cat].split('. '):
                if line.strip():
                    print(f"  │ {line.strip()}.")
            print(f"  │")
        
        # Status
        cat_passed = sum(1 for c in categories[cat] if c.passed)
        cat_total = len(categories[cat])
        cat_status = "✓ ALL PASSED" if cat_passed == cat_total else f"⚠ {cat_total - cat_passed} ISSUE(S)"
        print(f"  │ Status: {cat_status} ({cat_passed}/{cat_total})")
        print(f"  └{'─' * 50}")
        
        # Individual checks
        for check in categories[cat]:
            status = "✓" if check.passed else "✗"
            name = check.name.split(":")[-1] if ":" in check.name else check.name
            print(f"    {status} {name}: {check.message}")
    
    # Sensor summary table
    if report.sensor_summaries:
        print(f"\n7. SENSOR SUMMARY")
        print(subsep)
        print(f"  │ Coverage = (actual rows / expected rows) at 10-min intervals.")
        print(f"  └{'─' * 50}")
        print(f"    {'Sensor':<15} {'Rows':>10} {'Coverage':>10} {'Months':>8} {'Date Range':<25}")
        print(f"    {'-'*15} {'-'*10} {'-'*10} {'-'*8} {'-'*25}")
        
        for name, s in report.sensor_summaries.items():
            if s.date_range[0] != "N/A":
                date_str = f"{s.date_range[0][:10]} → {s.date_range[1][:10]}"
            else:
                date_str = "N/A"
            print(f"    {name:<15} {s.total_rows:>10,} {s.coverage_pct:>9.1f}% {len(s.parquet_files):>8} {date_str:<25}")
        
        # Column coverage bars
        if report.merged_summary.get("column_coverage"):
            print(f"\n    MERGED DATASET COLUMN COVERAGE:")
            for col, pct in report.merged_summary["column_coverage"].items():
                bar_len = int(pct / 5)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                print(f"      {col:<30} {bar} {pct:>5.1f}%")
    
    # Reference comparison
    if report.quality_metrics.get("scd41_2m_vs_lgr"):
        print(f"\n8. REFERENCE COMPARISON (SCD41 2m vs LGR)")
        print(subsep)
        print(f"  │ Bias = mean(sensor - reference); positive = sensor reads high.")
        print(f"  └{'─' * 50}")
        m = report.quality_metrics["scd41_2m_vs_lgr"]
        print(f"    n = {m['n_valid_pairs']:,} paired observations")
        print(f"    Bias:        {m['bias_ppm']:+.1f} ppm")
        print(f"    RMSE:        {m['rmse_ppm']:.1f} ppm")
        print(f"    MAE:         {m['mae_ppm']:.1f} ppm")
        print(f"    Correlation: {m['correlation']:.3f}")
        print(f"    Std:         {m['std_ppm']:.1f} ppm")
    
    # 30m comparisons
    sensor_30m = [k for k in report.quality_metrics if k.startswith("CO2_30M")]
    if sensor_30m:
        print(f"\n9. 30M SENSOR COMPARISONS (vs LGR)")
        print(subsep)
        # Header
        print(f"    {'Sensor':<12} {'n':>8} {'Bias':>10} {'RMSE':>10} {'Std':>8} {'Corr':>8}")
        print(f"    {'-'*12} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*8}")
        
        for key in sorted(sensor_30m):
            m = report.quality_metrics[key]
            sensor_name = key.replace("_vs_lgr", "").replace("CO2_30M_", "30M-")
            # Row
            print(f"    {sensor_name:<12} {m['n_valid_pairs']:>8,} {m['bias_ppm']:>+9.1f} {m['rmse_ppm']:>10.1f} {m['std_ppm']:>8.1f} {m['correlation']:>8.3f}")    
    # Verification checks
    if report.verification_checks:
        print(f"\n10. VERIFICATION CHECKS")
        print(subsep)
        print(f"  │ Checks for duplicate timestamps, time gaps, and empty columns.")
        print(f"  │ Time gaps are expected (WARNING); duplicates/invalid timestamps are CRITICAL.")
        print(f"  └{'─' * 50}")
        
        passed_count = sum(1 for c in report.verification_checks if c.passed)
        total_count = len(report.verification_checks)
        critical_issues = sum(1 for c in report.verification_checks 
                              if not c.passed and c.severity == Severity.CRITICAL)
        
        for check in report.verification_checks:
            if check.passed:
                status = "✓"
            elif check.severity == Severity.CRITICAL:
                status = "✗"
            else:
                status = "⚠"
            name = check.name.split(":")[-1] if ":" in check.name else check.name
            print(f"    {status} {name}: {check.message}")
        
        if passed_count == total_count:
            print(f"\n    All {total_count} verification checks passed.")
        elif critical_issues > 0:
            print(f"\n    {critical_issues} critical issue(s) require attention.")
        else:
            print(f"\n    {total_count - passed_count} warning(s) - time gaps expected given sensor coverage.")
    
    # Overall status
    status, message, counts = report.get_status()
    status_icon = {"PASSED": "✅", "PASSED_WITH_WARNINGS": "⚠️ ", "FAILED": "❌"}[status]
    
    print(f"\n{sep}")
    print(f"VALIDATION STATUS: {status_icon} {status}")
    print(f"  {message}")
    print(f"  Critical checks: {counts['critical_passed']}/{counts['critical_total']} passed")
    if counts['warning_total'] > 0:
        print(f"  Warning checks:  {counts['warning_passed']}/{counts['warning_total']} passed")
    print(f"  Total checks:    {counts['total_passed']}/{counts['total']} passed")
    print(sep)


def export_json(report, filepath: str | Path) -> Path:
    """Export report as JSON."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(report.to_dict(), f, indent=2, default=str)
    
    # print(f"JSON report exported: {filepath}")
    return filepath


def export_markdown(report, filepath: str | Path) -> Path:
    """Export report as Markdown using Jinja2 template."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Load template
    template_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(['html', 'xml']),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template("receipt.md.j2")
    
    # Prepare context
    status, status_message, counts = report.get_status()
    status_icon = {"PASSED": "✅", "PASSED_WITH_WARNINGS": "⚠️", "FAILED": "❌"}[status]
    
    # Year-month range
    if report.year_months:
        ym_range = f"{report.year_months[0][0]}-{report.year_months[0][1]} to {report.year_months[-1][0]}-{report.year_months[-1][1]}"
    else:
        ym_range = "No data found"
    
    context = {
        "timestamp": report.timestamp,
        "cfg": report.cfg,
        "merged_dir": report.merged_dir,
        "year_month_range": ym_range,
        "checks": report.checks,
        "sensor_summaries": report.sensor_summaries,
        "merged_summary": report.merged_summary,
        "quality_metrics": report.quality_metrics,
        "checksums": report.checksums,
        "verification_checks": report.verification_checks,
        "status": status,
        "status_icon": status_icon,
        "status_message": status_message,
        "counts": counts
    }
    
    # Render
    content = template.render(**context)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    # print(f"Markdown report exported: {filepath}")
    return filepath