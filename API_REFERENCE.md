# API Reference

Complete reference for the SMEAR Estonia CO2 Sensor Processing Pipeline.

## Table of Contents

- [Core Classes](#core-classes)
  - [PipelineConfig](#pipelineconfig)
  - [SensorConfig](#sensorconfig)
  - [SensorPipeline](#sensorpipeline)
  - [SensorMerger](#sensormerger)
- [Parsers](#parsers)
  - [BaseSensorParser](#basesensorparser)
  - [SCD41Parser](#scd41parser)
  - [LGRParser](#lgrparser)
- [Processing](#processing)
  - [DayProcessor](#dayprocessor)
  - [UptimeCalculator](#uptimecalculator)
- [Visualization](#visualization)
  - [UptimePlots](#uptimeplots)
  - [ValidationPlots](#validationplots)
  - [QualityControlPlots](#qualitycontrolplots)
- [Validation](#validation)
  - [ValidationReport](#validationreport)
  - [validate_outputs()](#validate_outputs)
- [Utility Functions](#utility-functions)
  - [merge_all_sensors()](#merge_all_sensors)

---

## Core Classes

### PipelineConfig

**Location:** `src/config.py`

Main configuration container for the entire processing pipeline.

```python
from src.config import PipelineConfig

# Load from YAML
config = PipelineConfig.from_yaml('config/sensors.yaml')

# Access properties
print(config.sensors_dir)      # Per-sensor output directory
print(config.merged_dir)       # Merged data directory
print(config.log_dir)          # Processing logs directory
print(config.sensors)          # List of SensorConfig objects
```

**Key Methods:**

- `from_yaml(config_path: Path) -> PipelineConfig`  
  Load configuration from YAML file

- `get_sensor_dirs(sensor_name: str) -> Dict[str, Path]`  
  Get directory paths for a sensor (base, csv, parquet, plots)

- `get_sensor_output_paths(sensor_name: str) -> Dict[str, Path]`  
  Get output file paths for a sensor (csv, uptime, directories)

- `get_merged_dirs() -> Dict[str, Path]`  
  Get directory paths for merged outputs

- `iter_sensor_csvs() -> Dict[str, Path]`  
  Iterate over all sensor 10min CSV paths

**Example Configuration (sensors.yaml):**

```yaml
sensors:
  - name: CO2_SCT1_2M
    sensor_type: scd41
    sensor_id: null
    input_dir: /data/raw/CO2-SCT1-2M
    altitude_m: 2.0
    expected_interval: 60
    co2_range: [350, 600]
    temp_range: [-40, 50]
    humidity_range: [0, 100]

sensors_dir: output/sensors
merged_dir: output/merged
log_dir: output/logs
validation_dir: output/validation
excluded_sensor_ids: []  # Optional: ['D'] to skip sensor D
```

---

### SensorConfig

**Location:** `src/config.py`

Configuration for a single sensor.

**Attributes:**

- `name: str` - Sensor identifier (e.g., 'CO2_SCT1_2M')
- `sensor_type: str` - Parser type ('scd41' or 'lgr_csv')
- `sensor_id: Optional[str]` - Sensor ID ('A', 'B', 'C', or None)
- `input_dir: Path` - Raw data directory
- `altitude_m: float` - Sensor height above ground
- `expected_interval: int` - Expected sampling interval in seconds
- `co2_range: Optional[tuple]` - Valid CO2 range (min, max) in ppm
- `temp_range: Optional[tuple]` - Valid temperature range (°C)
- `humidity_range: Optional[tuple]` - Valid humidity range (%)

---

### SensorPipeline

**Location:** `src/pipeline.py`

Orchestrates full sensor data processing workflow.

```python
from src.config import PipelineConfig
from src.pipeline import SensorPipeline

config = PipelineConfig.from_yaml('config/sensors.yaml')

# Create pipeline
pipeline = SensorPipeline(config, force=False)

# Process all sensors
pipeline.run_all(year=2024, month=9)

# Or process specific sensor
sensor_config = config.sensors[0]
pipeline.run_sensor(sensor_config, year=2024, month=9)
```

**Constructor:**

- `__init__(config: PipelineConfig, force: bool = False)`  
  - `force=True` reprocesses all days (overwrites existing data)
  - `force=False` (default) only processes new days (incremental)

**Key Methods:**

- `run_all(year: Optional[int] = None, month: Optional[int] = None)`  
  Process all sensors in configuration

- `run_sensor(sensor_config: SensorConfig, year: Optional[int], month: Optional[int])`  
  Process single sensor for specified period

**Outputs Generated:**

For each sensor:
- `{sensor}_10min.csv` - Main resampled data
- `{sensor}_uptime.csv` - Daily uptime statistics
- `{sensor}_{year}_{month}.csv` - Monthly CSV exports
- `{sensor}_{year}_{month}.parquet` - Monthly Parquet exports

---

### SensorMerger

**Location:** `src/merger.py`

Merge multiple sensor outputs into time-aligned dataset.

```python
from src.merger import SensorMerger, merge_all_sensors
from src.config import PipelineConfig

config = PipelineConfig.from_yaml('config/sensors.yaml')

# Method 1: Using convenience function (recommended)
merged_df = merge_all_sensors(
    config=config,
    start_date='2024-09-01',
    end_date='2024-09-30'
)

# Method 2: Using class directly
merger = SensorMerger(config=config)
sensor_csvs = config.iter_sensor_csvs()
merged_df = merger.merge_sensors(
    sensor_csvs,
    output_name='SMEAR_EE_CO2_merged.csv'
)
```

**Merge Strategy:**

- **OUTER JOIN** - All timestamps from all sensors preserved
- **No interpolation** - Missing data stays as NaN
- **Explicit gaps** - Data availability is transparent
- **Cross-sensor stats** - Computes cluster statistics for 30m sensors

**Key Methods:**

- `merge_sensors(sensor_csvs: Dict[str, Path], ...) -> pd.DataFrame`  
  Merge sensor CSVs into aligned dataset

- `export_monthly_csv(merged_df: pd.DataFrame, base_name: str)`  
  Export monthly subsets as separate CSV files

**Outputs Generated:**

- `SMEAR_EE_CO2_merged.csv` - Main merged dataset
- `SMEAR_EE_CO2_{year}_{month}_merged.csv` - Monthly CSV files
- `SMEAR_EE_CO2_{year}_{month}_merged.parquet` - Monthly Parquet files

---

## Parsers

### BaseSensorParser

**Location:** `src/parsers/base_parser.py`

Abstract base class defining parser interface. All sensor parsers must implement:

```python
from abc import ABC, abstractmethod

class CustomParser(BaseSensorParser):
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Parse file and return standardized DataFrame"""
        pass
    
    def get_file_pattern(self) -> str:
        """Return glob pattern for files"""
        pass
    
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract timestamp from filename"""
        pass
    
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add quality control flags"""
        pass
```

**Required Output Format:**

All parsers must return DataFrames with:
- `timestamp` column (datetime)
- Primary measurements (e.g., `co2`, `temp`, `humidity`)
- Corresponding QC flags (e.g., `co2_qc`, `temp_qc`)

---

### SCD41Parser

**Location:** `src/parsers/scd41_parser.py`

Parses NodeRED JSON format from SCD41 sensors.

```python
from src.parsers import SCD41Parser

parser = SCD41Parser(config, sensor_id='A')
df = parser.parse_file(Path('SCD41_A.json-2024-09-01'))
```

**File Format:**

```json
{"time": "2024-09-01 12:00:00", "co2": 420.5, "temp": 22.3, "humidity": 65.2}
{"time": "2024-09-01 12:01:00", "co2": 421.0, "temp": 22.4, "humidity": 65.1}
```

**Features:**

- Handles nested dict values: `{"value": 65.2, "status": "ok"}`
- Robust timestamp parsing
- Range validation with QC flags
- Malformed line handling

**File Pattern:** `SCD41_{ID}.json-*` where ID is 'A', 'B', 'C', or empty

---

### LGRParser

**Location:** `src/parsers/lgr_parser.py`

Parses LGR CSV format (27 columns).

```python
from src.parsers import LGRParser

parser = LGRParser(config)
df = parser.parse_file(Path('20240901000000.co2ch4'))
```

**Columns Parsed:**

Primary measurements:
- `CO2_dry` - Dry CO2 concentration (ppm)
- `CO2_dry_sd` - CO2 standard deviation
- `CH4_dry` - Dry CH4 concentration (ppm)
- `H2O_ppm` - Water vapor (ppm)
- `GasP_torr` - Gas pressure (torr)
- `GasT_C` - Gas temperature (°C)
- `AmbT_C` - Ambient temperature (°C)

Quality indicators:
- `quality` - LGR quality indicator (0-100)
- `Fit_Flag` - Fit quality flag (3 = good)

**File Pattern:** `*.co2ch4`

**Filename Format:** `YYYYMMDDHHMMSS.co2ch4`

---

## Processing

### DayProcessor

**Location:** `src/processor.py`

Processes single day of sensor data.

```python
from src.processor import DayProcessor

processor = DayProcessor(sensor_config)

# Process day's files
df_10min, uptime_stats = processor.process(
    files=[Path('file1.json'), Path('file2.json')],
    date_key=(2024, 9, 1)
)
```

**Processing Steps:**

1. Parse all files for the day
2. Combine and sort by timestamp
3. Remove duplicates (keep last)
4. Filter to day boundaries
5. Calculate uptime statistics
6. Resample to 10-minute intervals

**10-Minute Resampling:**

- **Origin:** Epoch-aligned (time synchronization across sensors)
- **Aggregations:**
  - Primary measurements: mean, std, count
  - Standard deviations: pooled SD (uncertainty propagation)
  - QC flags: most common flag per window

**Pooled SD Formula:**

```
pooled_sd = sqrt(sum(sd²)) / n
```

This correctly propagates uncertainty when averaging values with individual uncertainties.

---

### UptimeCalculator

**Location:** `src/uptime.py`

Calculates sensor uptime metrics.

```python
from src.uptime import UptimeCalculator

calc = UptimeCalculator(sensor_config)
stats = calc.calculate(df)

print(stats['uptime_ratio'])      # 0.957 (95.7% uptime)
print(stats['num_gaps'])          # 3 gaps
print(stats['max_gap_minutes'])   # 120 min (longest gap)
```

**Metrics Computed:**

- `uptime_ratio` - Time-based uptime (0-1)
- `sample_ratio` - Sample count vs expected
- `num_gaps` - Number of gaps > 2×expected_interval
- `max_gap_minutes` - Largest gap duration
- `detected_interval` - Median sampling interval
- `total_samples` - Actual sample count
- `expected_samples` - Expected sample count
- QC flag summaries per variable

---

## Visualization

### UptimePlots

**Location:** `src/visualization/uptime_plots.py`

Generate uptime analysis plots.

```python
from src.visualization import UptimePlots

plotter = UptimePlots(output_dir='plots/')

# Daily uptime timeseries
plotter.plot_timeseries('CO2_30M_A_uptime.csv', 'CO2_30M_A')

# Monthly heatmap
plotter.plot_heatmap('CO2_30M_A_uptime.csv', 'CO2_30M_A')

# Multi-sensor comparison
csvs = {
    'CO2_30M_A': Path('CO2_30M_A_uptime.csv'),
    'CO2_30M_B': Path('CO2_30M_B_uptime.csv')
}
plotter.plot_summary(csvs)
```

**Methods:**

- `plot_timeseries(uptime_csv, sensor_name, save=True) -> plt.Figure`  
  Daily uptime line plot with 95% threshold

- `plot_heatmap(uptime_csv, sensor_name, save=True) -> plt.Figure`  
  Monthly calendar heatmap (red=low, green=high)

- `plot_summary(uptime_csvs, save=True) -> plt.Figure`  
  Multi-sensor comparison (mean uptime + low-uptime days)

---

### ValidationPlots

**Location:** `src/visualization/validation_plots.py`

Compare test sensors against reference measurements.

```python
from src.visualization import ValidationPlots

plotter = ValidationPlots(output_dir='plots/')

# Timeseries overlay
csvs = {
    'LGR': Path('LGR_30M_10min.csv'),
    'SCD41_A': Path('CO2_30M_A_10min.csv')
}
plotter.plot_timeseries(csvs, start_date='2024-09-01', end_date='2024-09-30')

# Scatter plot (sensor vs reference)
plotter.plot_scatter(
    reference_csv=Path('LGR_30M_10min.csv'),
    test_csv=Path('CO2_30M_A_10min.csv'),
    reference_name='LGR',
    test_name='SCD41_A'
)

# Difference plot (bias analysis)
plotter.plot_difference(
    reference_csv=Path('LGR_30M_10min.csv'),
    test_csv=Path('CO2_30M_A_10min.csv'),
    reference_name='LGR',
    test_name='SCD41_A'
)
```

**Methods:**

- `plot_timeseries(data_csvs, start_date=None, end_date=None, save=True) -> plt.Figure`  
  Overlay multiple sensor timeseries

- `plot_scatter(reference_csv, test_csv, reference_name, test_name, save=True) -> plt.Figure`  
  Scatter plot with 1:1 line and statistics (R, RMSE, bias)

- `plot_difference(reference_csv, test_csv, reference_name, test_name, save=True) -> plt.Figure`  
  Two-panel plot: timeseries of difference + histogram

---

### QualityControlPlots

**Location:** `src/visualization/quality_control.py`

QC flag analysis plots.

```python
from src.visualization import QualityControlPlots

plotter = QualityControlPlots(output_dir='plots/')

# QC flag summary
plotter.plot_qc_summary('CO2_30M_A_10min.csv', 'CO2_30M_A')
```

---

## Validation

### ValidationReport

**Location:** `src/validation/report.py`

Orchestrates validation checks and report generation.

```python
from src.validation import ValidationReport

report = ValidationReport('config/sensors.yaml')
report.run_all()

# Access results
print(report.status)              # 'passed' or 'failed'
print(report.checks)              # List of CheckResult objects
print(report.sensor_summaries)    # Dict of sensor statistics
print(report.quality_metrics)     # Validation metrics

# Export
report.export_json('validation_report.json')
report.export_markdown('VALIDATION_RECEIPT.md')
report.print_summary()
```

**Checks Performed:**

1. Column names (no `<lambda>` artifacts)
2. File inventory (CSV/Parquet counts match)
3. Parquet integrity (schema, compression, timestamps)
4. CSV/Parquet consistency (values match)
5. Merged data (readability, coverage)
6. Data quality (gaps, sensor comparisons)
7. Verification (timestamps, duplicates)
8. Checksums (SHA256 for reproducibility)

---

### validate_outputs()

**Location:** `src/validation/__init__.py`

Convenience function to run validation and export reports.

```python
from src.validation import validate_outputs

# Default usage
report = validate_outputs()

# Custom config
report = validate_outputs(
    config_path='config/sensors.yaml',
    export_json=True,
    export_markdown=True,
    verbose=True
)
```

**Parameters:**

- `config_path` - Path to sensors.yaml (default: 'config/sensors.yaml')
- `export_json` - Export JSON report (default: True)
- `export_markdown` - Export Markdown receipt (default: True)
- `verbose` - Print summary to console (default: True)

**Returns:** `ValidationReport` object

---

## Utility Functions

### merge_all_sensors()

**Location:** `src/merger.py`

Convenience function to merge all sensors.

```python
from src.merger import merge_all_sensors
from src.config import PipelineConfig

config = PipelineConfig.from_yaml('config/sensors.yaml')

# Method 1: Use config (recommended)
merged = merge_all_sensors(
    config=config,
    start_date='2024-09-01',
    end_date='2024-09-30'
)

# Method 2: Explicit paths (legacy)
merged = merge_all_sensors(
    individual_dir=Path('output/individual'),
    sensor_names=['CO2_SCT1_2M', 'CO2_30M_A', 'LGR_30M'],
    output_dir=Path('output/merged')
)
```

**Parameters:**

- `config` - PipelineConfig object (preferred)
- `individual_dir` - Legacy: path to sensor CSV directory
- `sensor_names` - List of sensors to merge
- `start_date` - Optional date filter (YYYY-MM-DD)
- `end_date` - Optional date filter (YYYY-MM-DD)
- `output_dir` - Output directory for merged files
- `export_parquet` - Export monthly Parquet files (default: True)

**Returns:** `pd.DataFrame` with merged data

---

## Data Format Reference

### 10-Minute Resampled CSV

**Common Columns (SCD41):**

```
timestamp          - ISO 8601 timestamp (YYYY-MM-DD HH:MM:SS)
co2_mean          - Mean CO2 (ppm)
co2_std           - Std dev of CO2 within 10-min window
co2_count         - Number of raw measurements
co2_qc            - Quality flag (OK, BELOW_RANGE, ABOVE_RANGE, etc.)
temp_mean         - Mean temperature (°C)
temp_std          - Std dev of temperature
temp_count        - Number of measurements
temp_qc           - Temperature QC flag
humidity_mean     - Mean humidity (%)
humidity_std      - Std dev of humidity
humidity_count    - Number of measurements
humidity_qc       - Humidity QC flag
```

**LGR-Specific Columns:**

```
timestamp           - ISO 8601 timestamp
CO2_dry_mean       - Mean dry CO2 (ppm)
CO2_dry_sd         - Pooled SD (uncertainty)
CO2_dry_count      - Number of measurements
CH4_dry_mean       - Mean dry CH4 (ppm)
H2O_ppm_mean       - Mean water vapor (ppm)
GasP_torr_mean     - Mean gas pressure (torr)
GasT_C_mean        - Mean gas temperature (°C)
AmbT_C_mean        - Mean ambient temperature (°C)
quality_mean       - Mean LGR quality indicator
Fit_Flag           - Most common fit flag per window
```

### Quality Control Flags

- `OK` - Normal operation
- `BELOW_RANGE` - Value below expected range
- `ABOVE_RANGE` - Value above expected range
- `SPIKE` - Sudden change >500 ppm/min (SCD41 only)
- `NO_DATA` - No measurements in this window
- `LOW_QUALITY` - LGR quality <95 (LGR only)
- `BAD_FIT` - LGR fit flag ≠ 3 (LGR only)

---

## Complete Usage Example

```python
#!/usr/bin/env python3
"""Complete pipeline example"""

from src.config import PipelineConfig
from src.pipeline import SensorPipeline
from src.merger import merge_all_sensors
from src.validation import validate_outputs
from src.visualization import generate_all_plots

# 1. Load configuration
config = PipelineConfig.from_yaml('config/sensors.yaml')

# 2. Process all sensors
pipeline = SensorPipeline(config, force=False)
pipeline.run_all(year=2024, month=9)

# 3. Merge sensor outputs
merged = merge_all_sensors(
    config=config,
    start_date='2024-09-01',
    end_date='2024-09-30'
)

# 4. Validate outputs
report = validate_outputs(verbose=True)

# 5. Generate visualizations
generate_all_plots(config)

print("✓ Pipeline complete!")
```

---

## Error Handling

All major functions handle errors gracefully:

- **Parsing errors** → Skip malformed lines, log warnings
- **Missing files** → Log error, continue with other sensors
- **Invalid timestamps** → Mark as NaN, flag in QC
- **Data gaps** → Explicit NaN values, logged in uptime stats

Check logs in `output/logs/processing_*.log` for details.

---

## Performance Tips

1. **Incremental processing:** Use `force=False` (default) to only process new days
2. **Parquet for large datasets:** 10× smaller than CSV, faster to read
3. **Date filters:** Use `start_date`/`end_date` when merging to reduce memory
4. **Parallel processing:** Process sensors sequentially (each is independent)

---

## Support

- **Issues:** https://github.com/SMEAR-EE/SCD41_DATA/issues
- **Documentation:** See [README.md](README.md), [SETUP.md](SETUP.md), [APPLICATION_SUMMARY.md](APPLICATION_SUMMARY.md)
- **Examples:** [process_data.ipynb](process_data.ipynb)
