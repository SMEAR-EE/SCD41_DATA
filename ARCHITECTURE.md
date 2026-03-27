# Architecture Documentation

Technical architecture and design decisions for the SMEAR Estonia CO2 Sensor Processing Pipeline.

## Table of Contents

1. [System Overview](#system-overview)
2. [Data Flow](#data-flow)
3. [Directory Structure](#directory-structure)
4. [Component Architecture](#component-architecture)
5. [Design Patterns](#design-patterns)
6. [Time Synchronization](#time-synchronization)
7. [Quality Control](#quality-control)
8. [Extension Points](#extension-points)

---

## System Overview

The pipeline is a **batch-oriented ETL (Extract, Transform, Load) system** designed for processing multi-sensor atmospheric CO2 data.

### Key Characteristics

- **Incremental processing:** Only processes new data by default
- **Atomic operations:** Safe concurrent execution via temp files
- **Reproducibility:** Fixed algorithms, version-controlled, containerized
- **Scalability:** Processes data day-by-day to minimize memory usage
- **Fault tolerance:** Per-sensor error isolation, detailed logging

### Technology Stack

```
┌──────────────────────────────────────────────────────────┐
│                      Application Layer                    │
│  • Jupyter Notebook (process_data.ipynb)                 │
│  • Python Scripts (custom workflows)                     │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                     Processing Pipeline                   │
│  • Python 3.10+ (pandas, numpy, pyarrow)                 │
│  • Configuration: YAML (sensors.yaml)                    │
│  • Logging: Python logging module                        │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                       Data Storage                        │
│  • CSV (human-readable, universal)                       │
│  • Parquet (efficient, compressed, columnar)             │
│  • File system (local or NFS-mounted)                    │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                      Deployment Options                   │
│  • Local: Python venv                                    │
│  • Docker: Containerized environment                     │
│  • Docker Compose: Multi-service orchestration           │
└──────────────────────────────────────────────────────────┘
```

---

## Data Flow

### High-Level Flow

```
Raw Sensor Files → Parsing → Day Processing → 10-min Resampling → CSV/Parquet Export
       ↓              ↓            ↓                  ↓                    ↓
   SCD41.json    SCD41Parser   DayProcessor    Aggregation          Per-sensor
   LGR.co2ch4    LGRParser     Deduplication   Uncertainty           outputs
                                Filtering      Propagation
                                Uptime
                                Calculation
                                        ↓
                              ┌─────────────────┐
                              │  Time-aligned   │
                              │   10-min data   │
                              └─────────────────┘
                                        ↓
                              ┌─────────────────┐
                              │  SensorMerger   │
                              │  (Outer Join)   │
                              └─────────────────┘
                                        ↓
                              ┌─────────────────┐
                              │  Merged Dataset │
                              │  + Cluster Stats│
                              └─────────────────┘
                                        ↓
                              ┌─────────────────┐
                              │  Validation &   │
                              │  Visualization  │
                              └─────────────────┘
```

### Detailed Processing Stages

#### Stage 1: File Discovery & Grouping

```python
# Pipeline discovers files matching parser patterns
for sensor in sensors:
    parser = get_parser(sensor.sensor_type, sensor.sensor_id)
    files = sensor.input_dir.glob(parser.get_file_pattern())
    
    # Group by (year, month, day)
    daily_files = {}
    for file in files:
        dt = parser.extract_datetime_from_filename(file.name)
        key = (dt.year, dt.month, dt.day)
        daily_files[key].append(file)
```

**Input:** Raw sensor files (JSON or CSV)  
**Output:** `Dict[(year, month, day), List[Path]]`

---

#### Stage 2: Daily Parsing

```python
# DayProcessor processes one day at a time
for date_key, files in daily_files.items():
    # Parse all files for this day
    dfs = [parser.parse_file(f) for f in files]
    
    # Combine and deduplicate
    df_raw = pd.concat(dfs).sort_values('timestamp')
    df_raw = df_raw[~df_raw.index.duplicated(keep='last')]
    
    # Filter to day boundaries
    day_start = pd.Timestamp(year, month, day)
    day_end = day_start + pd.Timedelta(days=1)
    df_day = df_raw[(df_raw.index >= day_start) & (df_raw.index < day_end)]
```

**Input:** List of raw files for one day  
**Output:** Parsed, deduplicated, filtered DataFrame

---

#### Stage 3: Uptime Calculation

```python
# Calculate data availability metrics
uptime_stats = uptime_calculator.calculate(df_day)

# Returns:
# - uptime_ratio: Time-based uptime (0-1)
# - num_gaps: Count of gaps > 2×expected_interval
# - max_gap_minutes: Largest gap duration
# - QC summary statistics
```

**Input:** Single-day DataFrame  
**Output:** Dictionary of uptime metrics

---

#### Stage 4: 10-Minute Resampling

```python
# Resample to 10-min intervals (epoch-origin for synchronization)
df_10min = df_day.resample('10min', origin='epoch').agg({
    'co2': ['mean', 'std', 'count'],
    'co2_sd': _pooled_sd,  # Uncertainty propagation
    'temp': ['mean', 'std', 'count'],
    # ...
})

# QC flags: most common flag per window
df_10min['co2_qc'] = df_day['co2_qc'].resample('10min', origin='epoch').apply(
    lambda x: x.mode()[0] if len(x) > 0 else 'NO_DATA'
)
```

**Input:** Single-day DataFrame  
**Output:** 10-minute resampled DataFrame

**Key Design Decision:** Epoch-origin resampling ensures all sensors align to the same 10-minute boundaries (e.g., :00, :10, :20, ...).

---

#### Stage 5: CSV/Parquet Export

```python
# Append to main CSV (atomic via temp file)
df_10min.to_csv(temp_file, index=False, header=False)
with open(main_csv, 'ab') as f_out:
    with open(temp_file, 'rb') as f_in:
        f_out.write(f_in.read())

# Monthly Parquet export
for (year, month), group in df_full.groupby(['year', 'month']):
    table = pa.Table.from_pandas(group)
    pq.write_table(table, f"{sensor}_{year}_{month:02d}.parquet", 
                   compression='snappy')
```

**Input:** 10-minute resampled data  
**Output:** Per-sensor CSV and Parquet files

---

#### Stage 6: Multi-Sensor Merging

```python
# SensorMerger performs OUTER JOIN on timestamp
dfs = {sensor: pd.read_csv(csv) for sensor, csv in sensor_csvs.items()}

# Rename columns with sensor prefix
for sensor, df in dfs.items():
    df.columns = [f"{sensor.lower()}_{col}" for col in df.columns]

# Merge (preserves ALL timestamps)
merged = pd.concat(dfs.values(), axis=1, join='outer')

# Add cross-sensor statistics (30m cluster)
merged['scd41_30m_cluster_co2_mean'] = merged[co2_30m_cols].mean(axis=1)
merged['scd41_30m_cluster_co2_std'] = merged[co2_30m_cols].std(axis=1)
```

**Input:** Per-sensor 10-minute CSVs  
**Output:** Merged DataFrame with all sensors + cluster stats

**Key Design Decision:** OUTER JOIN preserves all timestamps from all sensors, making data gaps explicit rather than hiding them through interpolation.

---

## Directory Structure

### Per-Sensor Organization

```
output/
├── sensors/                    # Per-sensor outputs
│   ├── CO2_SCT1_2M/
│   │   ├── csv/
│   │   │   ├── CO2_SCT1_2M_10min.csv       # Main resampled data
│   │   │   ├── CO2_SCT1_2M_uptime.csv      # Daily uptime log
│   │   │   ├── CO2_SCT1_2M_2024_09.csv     # Monthly export
│   │   │   └── CO2_SCT1_2M_2024_10.csv
│   │   ├── parquet/
│   │   │   ├── CO2_SCT1_2M_2024_09.parquet # Compressed monthly
│   │   │   └── CO2_SCT1_2M_2024_10.parquet
│   │   └── plots/
│   │       ├── CO2_SCT1_2M_uptime_timeseries.png
│   │       └── CO2_SCT1_2M_uptime_heatmap.png
│   ├── CO2_30M_A/
│   │   └── ...
│   ├── CO2_30M_B/
│   │   └── ...
│   ├── CO2_30M_C/
│   │   └── ...
│   └── LGR_30M/
│       └── ...
├── merged/                     # Cross-sensor merged data
│   ├── csv/
│   │   ├── SMEAR_EE_CO2_merged.csv         # Main merged dataset
│   │   ├── SMEAR_EE_CO2_2024_09_merged.csv # Monthly export
│   │   └── SMEAR_EE_CO2_2024_10_merged.csv
│   └── parquet/
│       ├── SMEAR_EE_CO2_2024_09_merged.parquet
│       └── SMEAR_EE_CO2_2024_10_merged.parquet
├── validation/                 # Validation outputs
│   ├── validation_report.json
│   └── VALIDATION_RECEIPT.md
└── logs/                       # Processing logs
    ├── processing_20241027.log
    └── processing_20241028.log
```

**Advantages:**

1. **Isolation:** Each sensor's data is self-contained
2. **Scalability:** Easy to add/remove sensors
3. **Organization:** Outputs grouped by type (csv/parquet/plots)
4. **Clarity:** Directory name = sensor name

---

## Component Architecture

### Layer 1: Configuration

```
┌────────────────────────────────────┐
│        PipelineConfig              │
│  • Load from sensors.yaml          │
│  • Resolve paths                   │
│  • Create directories              │
│  • Provide sensor configs          │
└────────────────────────────────────┘
            ↓
┌────────────────────────────────────┐
│        SensorConfig                │
│  • name, sensor_type, sensor_id    │
│  • input_dir, altitude             │
│  • expected_interval               │
│  • Validation ranges               │
└────────────────────────────────────┘
```

**Responsibilities:**

- Parse YAML configuration
- Validate configuration parameters
- Provide paths to all components
- Create output directory structure

---

### Layer 2: Data Ingestion

```
┌────────────────────────────────────┐
│      BaseSensorParser (ABC)        │
│  • parse_file()                    │
│  • get_file_pattern()              │
│  • extract_datetime_from_filename()│
│  • add_qc_flags()                  │
└────────────────────────────────────┘
            ↓
    ┌───────────────┬────────────────┐
    ↓               ↓                ↓
┌──────────┐  ┌──────────┐  ┌────────────┐
│ SCD41    │  │   LGR    │  │  Custom    │
│ Parser   │  │  Parser  │  │  Parser    │
└──────────┘  └──────────┘  └────────────┘
```

**Responsibilities:**

- Parse sensor-specific file formats
- Extract timestamps from filenames
- Standardize DataFrame structure
- Add initial QC flags

**Design Pattern:** Strategy Pattern (parsers are interchangeable)

---

### Layer 3: Processing

```
┌────────────────────────────────────┐
│        SensorPipeline              │
│  • Orchestrate full workflow       │
│  • File discovery & grouping       │
│  • Incremental vs full processing  │
│  • Export coordination             │
└────────────────────────────────────┘
            ↓
┌────────────────────────────────────┐
│        DayProcessor                │
│  • Process single day              │
│  • Parse → Deduplicate → Filter   │
│  • Uptime → Resample → Return     │
└────────────────────────────────────┘
            ↓
┌────────────────────────────────────┐
│      UptimeCalculator              │
│  • Gap detection                   │
│  • Uptime metrics                  │
│  • QC flag summary                 │
└────────────────────────────────────┘
```

**Responsibilities:**

- Coordinate end-to-end processing
- Handle day-by-day iteration
- Manage incremental processing state
- Compute data quality metrics

**Design Pattern:** Template Method (DayProcessor follows fixed steps)

---

### Layer 4: Data Integration

```
┌────────────────────────────────────┐
│        SensorMerger                │
│  • Load per-sensor CSVs            │
│  • Outer join on timestamp         │
│  • Add cross-sensor statistics     │
│  • Export merged outputs           │
└────────────────────────────────────┘
```

**Responsibilities:**

- Time-align multiple sensors
- Preserve all timestamps (no interpolation)
- Compute cluster statistics
- Export merged datasets

**Design Pattern:** Facade (simplifies multi-sensor coordination)

---

### Layer 5: Visualization & Validation

```
┌────────────────────────────────────┐
│      BasePlotter (ABC)             │
│  • Consistent matplotlib styling   │
│  • Output directory management     │
└────────────────────────────────────┘
            ↓
    ┌──────────────┬─────────────┬──────────────┐
    ↓              ↓             ↓              ↓
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Uptime   │  │Validation│  │  Quality │  │  Taylor  │
│ Plots    │  │  Plots   │  │  Control │  │ Diagrams │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

┌────────────────────────────────────┐
│     ValidationReport               │
│  • Run all validation checks       │
│  • Generate reports (JSON/MD)      │
│  • Compute quality metrics         │
└────────────────────────────────────┘
```

**Responsibilities:**

- Generate publication-quality plots
- Validate data integrity
- Compute validation metrics
- Export reports for documentation

---

## Design Patterns

### 1. Strategy Pattern (Parsers)

Different sensor types require different parsing logic, but the interface is uniform:

```python
class BaseSensorParser(ABC):
    @abstractmethod
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        pass

# Usage
parser = get_parser(sensor_type)  # Returns SCD41Parser or LGRParser
df = parser.parse_file(file_path)  # Same interface
```

**Benefit:** Easy to add new sensor types without modifying existing code.

---

### 2. Template Method (DayProcessor)

Processing follows fixed steps, but subclasses could customize:

```python
def process(files, date_key):
    # 1. Parse
    dfs = [parser.parse_file(f) for f in files]
    
    # 2. Combine & deduplicate
    df = self._combine_and_deduplicate(dfs)
    
    # 3. Filter
    df = self._filter_to_day_boundaries(df, date_key)
    
    # 4. Calculate uptime
    uptime = self._calculate_uptime(df)
    
    # 5. Resample
    df_10min = self._resample_10min(df)
    
    return df_10min, uptime
```

**Benefit:** Consistent processing across sensors, easy to understand flow.

---

### 3. Facade Pattern (merge_all_sensors)

Simplifies complex multi-sensor merging:

```python
# Instead of:
merger = SensorMerger(config)
csvs = {s.name: paths[s.name] for s in sensors}
merged = merger.merge_sensors(csvs)
merger.export_monthly_csv(merged)

# Just:
merged = merge_all_sensors(config=config)
```

**Benefit:** Reduces boilerplate for common use cases.

---

### 4. Builder Pattern (Configuration)

YAML configuration builds complex PipelineConfig:

```yaml
sensors:
  - name: CO2_SCT1_2M
    sensor_type: scd41
    # ... many parameters
```

```python
config = PipelineConfig.from_yaml('config/sensors.yaml')  # Builds entire config
```

**Benefit:** Separates configuration from code, supports validation.

---

## Time Synchronization

### Challenge

Multiple sensors sample at different times:

```
SCD41_A: 12:00:37, 12:01:41, 12:02:39, ...  (irregular ~60s intervals)
SCD41_B: 12:00:12, 12:01:15, 12:02:18, ...  (irregular ~63s intervals)
LGR:     12:00:00, 12:01:00, 12:02:00, ...  (exact 60s intervals)
```

### Solution: Epoch-Origin Resampling

```python
# Resample with origin='epoch' aligns all sensors to same boundaries
df_10min = df.resample('10min', origin='epoch').agg(...)

# Results:
# 12:00:00 - aggregates measurements from 12:00:00 to 12:09:59
# 12:10:00 - aggregates measurements from 12:10:00 to 12:19:59
# ...
```

**All sensors** use the same boundaries, enabling direct comparison.

### Visualization

```
Raw timestamps (sensor A):
├─ 12:00:37
├─ 12:01:41
├─ 12:02:39
├─ 12:03:44
├─ 12:04:52
├─ 12:05:59
├─ 12:07:03
├─ 12:08:11
├─ 12:09:15

Resampled (10-min):
├─ 12:00:00 ──┐
├─ 12:10:00   │← Mean of all measurements in [12:00:00, 12:10:00)
├─ 12:20:00   │
```

---

## Quality Control

### Multi-Level QC Strategy

#### Level 1: Parsing (Real-time)

```python
# Range validation during parsing
if value < min_val or value > max_val:
    qc_flag = 'ABOVE_RANGE' if value > max_val else 'BELOW_RANGE'
else:
    qc_flag = 'OK'
```

**Applied:** During file parsing  
**Output:** QC flags in parsed DataFrame

---

#### Level 2: Spike Detection (SCD41)

```python
# Detect sudden jumps
diff = df['co2'].diff()
if abs(diff) > 500:  # >500 ppm/min change
    qc_flag = 'SPIKE'
```

**Applied:** During parsing  
**Output:** Additional QC flags

---

#### Level 3: Instrument Quality (LGR)

```python
# LGR-specific quality indicators
if quality < 95:
    qc_flag = 'LOW_QUALITY'
if fit_flag != 3:
    qc_flag = 'BAD_FIT'
```

**Applied:** During LGR parsing  
**Output:** LGR-specific QC flags

---

#### Level 4: Uptime Analysis

```python
# Gap detection
gaps = time_diffs[time_diffs > 2 * expected_interval]
uptime_ratio = (total_time - downtime) / total_time
```

**Applied:** During day processing  
**Output:** Uptime statistics logged to CSV

---

#### Level 5: Validation Checks

```python
# Post-processing validation
- Column name integrity
- Parquet schema validation
- CSV/Parquet consistency
- Merged data coverage
- Sensor vs reference comparison
```

**Applied:** After processing complete  
**Output:** ValidationReport with pass/fail status

---

## Extension Points

### Adding a New Sensor Type

```python
# 1. Create new parser
class NewSensorParser(BaseSensorParser):
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        # Custom parsing logic
        pass
    
    def get_file_pattern(self) -> str:
        return "*.newsensor"
    
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        # Extract timestamp
        pass
    
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        # Add QC logic
        pass

# 2. Register in config
sensors:
  - name: NEW_SENSOR
    sensor_type: newsensor  # ← Add to processor
    input_dir: /path/to/data
    # ...

# 3. Update DayProcessor (if needed)
if config.sensor_type == 'newsensor':
    parser = NewSensorParser(config)
```

---

### Adding a New Plot Type

```python
# 1. Create plotter class
class CustomPlots(BasePlotter):
    def plot_custom(self, data_csv: Path, save: bool = True):
        df = pd.read_csv(data_csv)
        fig, ax = plt.subplots()
        # ... plotting logic ...
        if save:
            self._save_figure(fig, "custom_plot.png")
        return fig

# 2. Use in pipeline
from visualization import CustomPlots

plotter = CustomPlots(output_dir='plots/')
plotter.plot_custom('sensor_data.csv')
```

---

### Adding a New Validation Check

```python
# 1. Add check function to src/validation/checks.py
def check_custom(cfg) -> list[CheckResult]:
    """Custom validation check"""
    results = []
    # ... check logic ...
    results.append(CheckResult(
        name="custom_check",
        passed=True,
        message="Check passed",
        details={},
        severity=Severity.INFO
    ))
    return results

# 2. Register in ValidationReport.run_all()
def run_all(self):
    # ...
    self.checks.extend(check_custom(self.cfg))
```

---

## Performance Considerations

### Memory Management

- **Day-by-day processing:** Avoids loading entire dataset into memory
- **Streaming CSV writes:** Uses temp files for atomic appends
- **Parquet compression:** Reduces storage by ~10× vs CSV

### I/O Optimization

- **Incremental processing:** Only reads new days (checks uptime log)
- **Batch writes:** Writes entire day at once, not per-file
- **Compression:** Snappy compression for fast read/write

### Scalability

Current implementation scales to:
- **Sensors:** 5-10 sensors (tested with 5)
- **Duration:** Years of continuous data (tested with months)
- **File size:** Individual files up to ~100 MB
- **Total dataset:** Gigabytes (merged CSV ~50 MB for 1 month, 5 sensors)

---

## Error Handling Philosophy

### Fail-Safe Approach

1. **Per-sensor isolation:** One sensor failure doesn't stop others
2. **Detailed logging:** All errors logged with stack traces
3. **Graceful degradation:** Skip invalid files, continue processing
4. **Atomic operations:** Temp files prevent partial writes
5. **Validation layer:** Post-processing checks catch issues

### Example

```python
for sensor in sensors:
    try:
        pipeline.run_sensor(sensor, year, month)
    except Exception as e:
        logger.error(f"Failed: {sensor.name}: {e}", exc_info=True)
        # Continue with next sensor
```

---

## Future Enhancements

Potential architecture improvements:

1. **Parallel processing:** Process sensors in parallel (multiprocessing)
2. **Streaming processing:** Real-time processing as files arrive
3. **Database backend:** PostgreSQL/TimescaleDB for large deployments
4. **API server:** REST API for remote processing
5. **Web dashboard:** Interactive visualization of results
6. **Automated QC:** Machine learning-based anomaly detection

---

## References

- **Pandas resampling:** https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
- **PyArrow Parquet:** https://arrow.apache.org/docs/python/parquet.html
- **Python logging:** https://docs.python.org/3/library/logging.html
- **YAML config:** https://pyyaml.org/wiki/PyYAMLDocumentation
