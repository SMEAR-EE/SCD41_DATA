# Validation Module

Validates processed CO2 sensor data and generates receipts for data management documentation.

## Usage

```python
from src.validation import validate_outputs

# Run with default config (config/sensors.yaml)
validate_outputs()

# Custom config
validate_outputs("path/to/sensors.yaml")

# Suppress console output
validate_outputs(verbose=False)

# Skip exports
validate_outputs(export_json=False, export_markdown=False)
```

## Outputs

| File | Location | Purpose |
|------|----------|---------|
| Console summary | stdout | Quick review |
| `validation_report.json` | `output/validation/` | Machine-readable, CI integration |
| `VALIDATION_RECEIPT.md` | `output/validation/` | Documentation, data management |

## Checks Performed

1. **Column names** — No `<lambda>` artifacts from pandas bugs
2. **File inventory** — CSV/Parquet counts match per sensor
3. **Parquet integrity** — Valid schema, timestamp column, compression
4. **CSV/Parquet consistency** — Row counts and values match
5. **Merged data** — Combined dataset readable, date range valid
6. **Quality metrics** — Time gaps, sensor vs reference comparison
7. **Checksums** — SHA256 for merged CSV

## Customising the Receipt

Edit `src/validation/templates/receipt.md.j2` (Jinja2 template).

Available variables:
- `{{ cfg.sensors_dir }}`, `{{ merged_dir }}`
- `{{ sensor_summaries }}` — dict of SensorSummary objects
- `{{ quality_metrics }}` — comparison statistics
- `{{ checks }}` — list of CheckResult objects
- `{{ status }}`, `{{ status_icon }}`, `{{ counts }}`

## Package Structure

```
src/validation/
├── __init__.py      # Public API: validate_outputs()
├── models.py        # Severity, CheckResult, SensorSummary
├── checks.py        # Validation logic
├── report.py        # Orchestrator
├── output.py        # Formatters
└── templates/
    └── receipt.md.j2
```

## Dependencies

- pandas, numpy, pyarrow, pyyaml, jinja2