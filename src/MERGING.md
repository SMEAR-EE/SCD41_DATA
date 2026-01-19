# Data Merging Documentation

## Overview

The sensor data merger performs time-alignment of multiple independent sensor datasets into a unified analysis-ready format. This document explains the merge behaviour.

## Merge Strategy: OUTER JOIN

### What is an Outer Join?

The merger uses a **full outer join** on timestamps, which means:

```
OUTER JOIN = ALL timestamps from ALL sensors are preserved
```

### Example

Consider three sensors measuring at different times:

**LGR (reference):**
```
2024-09-01 12:00:00 → CO2: 420.5 ppm
2024-09-01 12:10:00 → CO2: 421.2 ppm
2024-09-01 12:20:00 → CO2: 419.8 ppm
```

**SCD41_A (test sensor):**
```
2024-09-01 12:00:00 → CO2: 418.3 ppm
2024-09-01 12:20:00 → CO2: 417.9 ppm
(missing 12:10:00 - sensor downtime)
```

**Merged Result:**
```
timestamp            | lgr_co2  | scd41_a_co2 | Notes
---------------------|----------|-------------|------------------------
2024-09-01 12:00:00  | 420.5    | 418.3       | Both sensors present
2024-09-01 12:10:00  | 421.2    | NaN         | SCD41_A has gap
2024-09-01 12:20:00  | 419.8    | 417.9       | Both sensors present
```

## Key Principles

### 1. No Data Interpolation

**Missing data stays missing (NaN).** We do NOT:
- Interpolate between adjacent values
- Forward-fill gaps
- Use default values

**Why:** Interpolation would hide sensor failures and create artificial data points that could bias validation statistics.

### 2. Explicit Data Availability

Coverage statistics show exactly what data exists:

```python
# Example from September 2024 merge:
CO2_30M_A: 168/4177 timestamps (4.0% coverage)
CO2_30M_B: 367/4177 timestamps (8.8% coverage)
LGR_30M:   4081/4177 timestamps (97.7% coverage)
```

This transparency allows:
- Identifying periods of poor sensor availability
- Understanding confidence in validation metrics
- Proper statistical treatment of missing data

### 3. Cluster Statistics Handle Missing Data

For the 30m sensor cluster (3 co-located SCD41 sensors), statistics are computed only from available data:

```python
# If only 2 of 3 sensors have data at 12:00:00:
cluster_mean = mean(sensor_A, sensor_B)      # Average of available sensors
cluster_std = std(sensor_A, sensor_B)        # Std of available sensors
cluster_count = 2                             # Number reporting
```

**If only 1 sensor reports:**
```python
cluster_mean = sensor_A                       # Single value
cluster_std = NaN                             # Cannot compute std from 1 point
cluster_count = 1                             # Only 1 reporting
```

**If no sensors report:**
```python
cluster_mean = NaN
cluster_std = NaN
cluster_count = 0
```

## Data Quality Indicators

Every merged dataset includes quality control flags from individual sensors:

```
co2_30m_a_co2_qc     → Quality flag from sensor A
co2_30m_a_co2_mean   → Mean CO2 value
co2_30m_a_co2_std    → Within-bin standard deviation
co2_30m_a_co2_count  → Number of raw measurements in bin
```

### QC Flag Meanings

- `OK`: Normal operation
- `BELOW_RANGE`: Value below expected range
- `ABOVE_RANGE`: Value above expected range
- `SPIKE`: Sudden change >500 ppm/min
- `NO_DATA`: No measurements in this bin
- `LOW_QUALITY`: LGR quality indicator <95
- `BAD_FIT`: LGR fit flag ≠ 3

## File Outputs

### 1. Main Merged CSV
`SMEAR_EE_CO2_merged.csv`
- Complete dataset for all requested dates
- One row per 10-minute timestamp
- Columns prefixed by sensor name

### 2. Monthly CSV Exports
`SMEAR_EE_CO2_2024_09_merged.csv`
- Subset for each month
- Identical format to main file
- Convenient for analysis of specific periods

### 3. Monthly Parquet Exports (NEW)
`SMEAR_EE_CO2_2024_09_merged.parquet`
- Binary columnar format
- ~10x smaller than CSV (snappy compression)
- Faster to read in Python/R
- Preserves data types exactly
- Recommended for large-scale analysis

## Usage Examples

### Reading Merged Data

**CSV (Python):**
```python
import pandas as pd

# Load merged data
df = pd.read_csv('output/merged/SMEAR_EE_CO2_merged.csv', 
                 parse_dates=['timestamp'])

# Check coverage
print(df['lgr_30m_co2_dry_mean'].notna().sum(), "LGR timestamps")
print(df['co2_30m_a_co2_mean'].notna().sum(), "SCD41_A timestamps")
```

**Parquet (Python):**
```python
import pandas as pd

# Faster and automatic type inference
df = pd.read_parquet('output/merged/parquet/SMEAR_EE_CO2_2024_09_merged.parquet')
```

**R:**
```r
library(arrow)

# Read parquet efficiently
df <- read_parquet('output/merged/parquet/SMEAR_EE_CO2_2024_09_merged.parquet')
```

### Filtering Valid Data

```python
# Only timestamps where both LGR and SCD41_A have valid data
valid_comparison = df[
    df['lgr_30m_co2_dry_mean'].notna() & 
    df['co2_30m_a_co2_mean'].notna() &
    (df['lgr_30m_co2_qc'] == 'OK') &
    (df['co2_30m_a_co2_qc'] == 'OK')
]

print(f"Valid comparison points: {len(valid_comparison)}")
```

### Computing Validation Metrics

```python
# Compare SCD41 cluster mean to LGR reference
comparison = df[
    df['scd41_30m_cluster_co2_mean'].notna() & 
    df['lgr_30m_co2_dry_mean'].notna()
].copy()

comparison['difference'] = (
    comparison['scd41_30m_cluster_co2_mean'] - 
    comparison['lgr_30m_co2_dry_mean']
)

print(f"Mean bias: {comparison['difference'].mean():.2f} ppm")
print(f"RMSE: {np.sqrt((comparison['difference']**2).mean()):.2f} ppm")
```

## Reproducibility

All merge operations are:
- **Deterministic**: Same inputs → same outputs
- **Logged**: Merge quality reports in processing logs
- **Versioned**: Merge code is version-controlled
- **Documented**: This file + code docstrings

The merge can be reproduced by:
1. Running individual sensor processing pipeline
2. Calling `merge_all_sensors()` with same parameters
3. Results will be identical (byte-for-byte)

## References

For questions about merge behaviour or data interpretation:
- Code: `src/merger.py`
- Logs: `output/logs/processing_*.log`
- This documentation: `docs/MERGING.md`