# %% [markdown]
# ## Data Validation Receipt
# 
# Generate a comprehensive validation report for processed outputs.

# %%
from src.validation import validate_outputs, ValidationReport

# Quick one-liner: runs all checks, prints summary, exports JSON + Markdown
report = validate_outputs(output_dir="output")

# %% [markdown]
# ### Alternative: Granular control

# %%
# For more control over what gets run/exported:
report = ValidationReport(output_dir="output")

# Run individual checks
report.check_column_names()
report.check_file_inventory()
report.validate_parquet_files()
report.check_csv_parquet_consistency()
report.validate_merged_data()
report.compute_quality_metrics()
report.compute_checksums(include_all=True)  # Checksum all parquets

# Print to console
report.print_summary()

# Export reports
report.export_json("output/validation_report.json")
report.export_markdown("output/VALIDATION_RECEIPT.md")

# %% [markdown]
# ### Accessing results programmatically

# %%
# Check results are available as structured data
print(f"Total checks: {len(report.checks)}")
print(f"Passed: {sum(1 for c in report.checks if c.passed)}")

# Access sensor summaries
for sensor, summary in report.sensor_summaries.items():
    print(f"{sensor}: {summary.total_rows} rows, {summary.coverage_pct:.1f}% coverage")

# Access quality metrics
if "scd41_2m_vs_lgr" in report.quality_metrics:
    metrics = report.quality_metrics["scd41_2m_vs_lgr"]
    print(f"SCD41 2m bias vs LGR: {metrics['bias_ppm']:.1f} ppm")

# %%
