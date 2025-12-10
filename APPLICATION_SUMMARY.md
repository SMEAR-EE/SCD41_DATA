# SMEAR Estonia CO2 Sensor Data Processing Pipeline

## Overview

**SMEAR Estonia CO2 Sensor Processing** is a fast, reproducible Python-based data processing pipeline designed for atmospheric CO2 monitoring at the SMEAR Estonia research station. The application processes data from multiple CO2 sensors (SCD41 and LGR) and produces time-synchronized, quality-controlled datasets suitable for scientific analysis.

**Repository**: SMEAR-EE/SCD41_DATA  
**License**: MIT License (Copyright 2025 Matevž Borjan Zorec)  
**Python Version**: 3.10+ (Docker image uses 3.12)

---

## Purpose & Research Context

This pipeline is designed for the SMEAR (Station for Measuring Ecosystem-Atmosphere Relations) Estonia site, processing continuous CO2 measurements from:
- **4x SCD41 sensors** (Sensirion low-cost CO2 sensors at 2m and 30m heights)
- **1x LGR sensor** (Los Gatos Research high-precision reference instrument at 30m)

The data supports atmospheric CO2 research and sensor validation studies, with anticipated publication (citation pending).

---

## Key Features

### 1. **Multi-Sensor Data Processing**
- Processes 5 sensors simultaneously (4 SCD41 + 1 LGR reference)
- Handles two different data formats:
  - SCD41: NodeRED JSON format with robust dict/value extraction
  - LGR: CSV format with 27 columns including CH4, CO2, H2O, and meteorological data
- Configurable per-sensor parameters (altitude, expected intervals, valid ranges)
- Support for sensor exclusion (e.g., sensor ID 'D' can be skipped)

### 2. **Time Synchronization & Resampling**
- Resamples all sensors to **10-minute intervals** with epoch-origin alignment
- Ensures time synchronization across all sensors for comparative analysis
- Proper statistical aggregation:
  - Mean, standard deviation, and count for primary measurements
  - Uncertainty propagation for standard deviation fields (sqrt(sum(sd²))/n)
  - QC flag summary (most common flag per window)

### 3. **Data Quality Control**
- **Uptime tracking**: Monitors data availability, gap detection, and temporal coverage
- **Range validation**: Configurable min/max thresholds per variable (CO2, temperature, humidity)
- **QC flagging system**: Tracks data quality flags through the processing chain
- **Duplicate removal**: Automatically detects and removes duplicate timestamps
- **Gap analysis**: Identifies and logs data gaps exceeding expected sampling intervals

### 4. **Robust Data Management**
- **Incremental processing**: Only processes new days (unless force=True)
- **Atomic writes**: Uses temporary files for safe CSV appending
- **Output formats**:
  - CSV files for individual sensors (time-series)
  - Parquet files for monthly data (compressed with Snappy)
  - Uptime logs tracking daily statistics
- **Smart sorting**: Automatically sorts output if timestamps are out of order

### 5. **Comprehensive Visualization**
Modular plotting system with multiple plot types:
- **Uptime Plots**:
  - Time series showing data availability
  - Heatmaps for visual gap identification
  - Multi-sensor summary comparisons
- **Validation Plots**:
  - Time series overlays for sensor comparison
  - Scatter plots (sensor vs. reference)
  - Difference plots (bias analysis)
- **Quality Control Plots**:
  - QC flag summaries
  - Distribution analysis
- **Taylor Diagrams**: Statistical comparison framework (noted as non-functional in current version)

### 6. **Data Merging**
- `SensorMerger` class for combining multiple sensor outputs
- Time-aligned datasets for cross-sensor analysis
- Configurable date range filtering
- Column renaming to avoid conflicts

### 7. **Production-Ready Architecture**

**Deployment Options**:
- Local execution with virtual environment
- Docker containerization with multi-stage builds
- Docker Compose orchestration with volume mounting

**Logging & Monitoring**:
- Structured logging to files and console
- Daily uptime statistics
- Warning flags for low uptime (<95%)
- Processing progress tracking

**Configuration Management**:
- YAML-based configuration (`config/sensors.yaml`)
- Separate settings per sensor
- Centralized output directory management
- Environment variable support in Docker

---

## Architecture

### Core Components

1. **Pipeline (`pipeline.py`)**
   - `SensorPipeline`: Orchestrates full processing workflow
   - Manages file discovery, grouping by day, and output export
   - Handles incremental vs. full reprocessing

2. **Processor (`processor.py`)**
   - `DayProcessor`: Processes single day of sensor data
   - Handles parsing, deduplication, uptime calculation, and resampling

3. **Parsers (`parsers/`)**
   - `BaseSensorParser`: Abstract base class defining parser interface
   - `SCD41Parser`: Parses NodeRED JSON format, handles nested dict values
   - `LGRParser`: Parses LGR CSV format with 27-column structure

4. **Uptime Calculator (`uptime.py`)**
   - `UptimeCalculator`: Computes uptime metrics
   - Gap detection, interval validation, QC summary statistics

5. **Visualization (`visualization/`)**
   - Modular plotting system with base styling
   - Separate modules for uptime, validation, QC, and Taylor diagrams

6. **Merger (`merger.py`)**
   - `SensorMerger`: Combines multiple sensor outputs
   - Time-alignment and conflict resolution

7. **Configuration (`config.py`)**
   - `PipelineConfig`: Main configuration container
   - `SensorConfig`: Per-sensor settings

### Data Flow

```
Raw Sensor Files → Parser → DayProcessor → 10-min Resampling → CSV/Parquet
                                   ↓
                            Uptime Tracking
                                   ↓
                            QC Flag Summary
                                   ↓
                          Visualization & Merging
```

---

## Directory Structure

```
SCD41_DATA/
├── src/
│   ├── pipeline.py          # Main orchestration
│   ├── processor.py         # Daily data processing
│   ├── config.py            # Configuration management
│   ├── uptime.py            # Uptime metrics
│   ├── merger.py            # Multi-sensor merging
│   ├── logging_utils.py     # Logging setup
│   ├── parsers/
│   │   ├── base_parser.py   # Parser interface
│   │   ├── scd41_parser.py  # SCD41 JSON parser
│   │   └── lgr_parser.py    # LGR CSV parser
│   └── visualization/
│       ├── base_plotter.py  # Common styling
│       ├── uptime_plots.py  # Uptime visualizations
│       ├── validation_plots.py  # Validation plots
│       ├── quality_control.py   # QC plots
│       └── taylor_plots.py      # Taylor diagrams
├── config/
│   └── sensors.example.yaml # Configuration template
├── output/
│   ├── individual/          # Per-sensor CSV files
│   ├── parquet/             # Monthly Parquet files
│   ├── plots/               # Generated plots
│   └── logs/                # Processing logs
├── testing/
│   ├── process_data.ipynb   # Example Jupyter notebook
│   └── prototype/           # Development notebooks
├── Dockerfile               # Container definition
├── docker-compose.yaml      # Orchestration config
├── requirements_dev.txt     # Python dependencies
└── README.md                # Quick start guide
```

---

## Technologies & Dependencies

### Core Libraries
- **pandas** (2.3.3): Time series data manipulation
- **numpy** (2.3.5): Numerical operations and uncertainty propagation
- **pyarrow** (22.0.0): Efficient Parquet file I/O with compression
- **PyYAML** (6.0.3): Configuration file parsing

### Visualization
- **matplotlib** (3.10.7): Base plotting
- **seaborn** (0.13.2): Statistical visualizations
- **SkillMetrics** (1.2.4): Taylor diagram framework

### Development & Analysis
- **jupyter** (ipykernel 7.1.0): Interactive analysis
- **IPython** (9.8.0): Enhanced REPL

### Deployment
- **Docker**: Python 3.12-slim base image
- **Docker Compose**: Multi-container orchestration

---

## Typical Workflow

1. **Setup** (one-time):
   - Clone repository
   - Run `./setup.sh` to create virtual environment
   - Configure `config/sensors.yaml` with data paths

2. **Processing**:
   - Activate environment: `source venv/bin/activate`
   - Run Jupyter notebook: `jupyter notebook testing/process_data.ipynb`
   - Or use Docker: `docker-compose up`

3. **Output**:
   - Processed CSVs: `output/individual/`
   - Monthly Parquets: `output/parquet/`
   - Plots: `output/plots/`
   - Logs: `output/logs/`

4. **Reprocessing**:
   - Set `force=True` in pipeline initialization
   - Specify year/month to reprocess specific periods

---

## Performance Characteristics

- **Incremental processing**: Only processes new data by default
- **Efficient I/O**: Parquet compression reduces storage footprint
- **Memory efficient**: Processes data day-by-day
- **Fast startup**: ~5 minutes from clone to first results
- **Scalable**: Designed for continuous, long-term datasets

---

## Quality Assurance Features

1. **Data Validation**:
   - Configurable range checks per variable
   - Automatic duplicate detection and removal
   - Missing data flagging

2. **Traceability**:
   - Daily uptime logs with timestamp
   - Processing logs with warnings and errors
   - Version control ready (Git)

3. **Reproducibility**:
   - Fixed random seed behavior (epoch-aligned resampling)
   - Containerized environment (Docker)
   - Configuration-driven processing

4. **Error Handling**:
   - Graceful failure per sensor (continues processing others)
   - Detailed error logging with stack traces
   - Atomic file writes prevent corruption

---

## Extensibility

The pipeline is designed for easy extension:

- **New sensor types**: Implement `BaseSensorParser` interface
- **Custom plots**: Add methods to visualization modules or create new modules
- **Additional QC checks**: Extend `UptimeCalculator` or `DayProcessor`
- **Alternative outputs**: Modify export methods in `SensorPipeline`
- **Post-processing**: Use `SensorMerger` or add new analysis modules

---

## Current Limitations & Known Issues

1. **Taylor diagram visualization**: Noted as non-functional in current version
2. **Single-site focus**: Optimized for SMEAR Estonia station
3. **File format specificity**: Parsers designed for NodeRED JSON and LGR CSV formats
4. **No real-time processing**: Batch-oriented, not streaming

---

## Use Cases

1. **Atmospheric Research**: Long-term CO2 monitoring and trend analysis
2. **Sensor Validation**: Comparing low-cost SCD41 sensors against LGR reference
3. **Quality Control**: Identifying data gaps and sensor issues
4. **Data Publication**: Generating standardized datasets for data repositories
5. **Operational Monitoring**: Tracking sensor network health and uptime

---

## Summary

The SMEAR Estonia CO2 Sensor Processing Pipeline is a **production-ready, scientifically rigorous tool** for processing multi-sensor atmospheric CO2 data. It combines:
- ✅ Robust data ingestion from heterogeneous sources
- ✅ Time-synchronized resampling with proper uncertainty propagation
- ✅ Comprehensive quality control and uptime tracking
- ✅ Multiple output formats (CSV, Parquet)
- ✅ Rich visualization capabilities
- ✅ Docker deployment support
- ✅ Incremental processing for efficiency
- ✅ Modular, extensible architecture

The pipeline successfully bridges the gap between raw sensor output and analysis-ready datasets, supporting both operational monitoring and scientific research at the SMEAR Estonia atmospheric research station.
