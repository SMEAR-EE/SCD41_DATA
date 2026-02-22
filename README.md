# SMEAR Estonia CO2 Sensor Processing

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/SMEAR-EE/SCD41_DATA/releases/tag/v0.2.0)
[![License](https://img.shields.io/badge/license-Apache_2.0-white.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Fast, light and reproducible post-processing pipeline for SCD41 and LGR CO2 raw sensor data at the Estonian Station for Measuring Ecosystem-Atmosphere Relations (SMEAR; [smear.emu.ee](https://smear.emu.ee/)).

> **Status:** v0.2.0 - Stable release with comprehensive validation suite and enhanced data quality reporting

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Configure sensors
edit config/sensor_config.yaml  # Set your data paths

# 4. Run processing
jupyter notebook process_data.ipynb
```

Processed data appears in `output/`.

## What It Does

Processes many sensors (4x SCD41, 1x LGR reference) with:
- **Time-synced resampling** to 10-min intervals (epoch-aligned)
- **Quality control** tracking uptime, data quality flags, validation report
- **Comprehensive validation** suite with JSON/Markdown reports and coverage metrics
- **Multi-out** CSV and Parquet formats
- **Visuals** uptime, validation, and QC plots

## (Default) Output Structure

| Output | Location |
|--------|----------|
| Sensors | `output/sensors/` |
| Merged | `output/merged/` |
| Validation | `output/validation/` |
| Logs | `output/logs/` |

## Configuration

Edit `config/sensor_config.yaml` to set input data paths:
```yaml
sensors:
  - name: CO2_SCT1_2M
    input_dir: /path/to/your/data  # ← Change this
    sensor_type: scd41
    # Other settings auto-configured
```

## Documentation

- **Quick Start**: This README (you are here!)
- **Setup Guide**: [`SETUP.md`](SETUP.md) - Installation, configuration, and troubleshooting
- **API Reference**: [`API_REFERENCE.md`](API_REFERENCE.md) - Complete API docs for all classes and functions
- **Architecture**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - Technical design, data flow, and component architecture
- **Output Schema**: [`OUTPUT_SCHEMA.md`](OUTPUT_SCHEMA.md) - Detailed column definitions and data formats
- **Application Summary**: [`src/APPLICATION_SUMMARY.md`](src/APPLICATION_SUMMARY.md) - Overviews features & research context
- **Data Merging**: [`src/MERGING.md`](src/MERGING.md) - Information on sensor data merging
- **Visualization**: [`src/visualization/PLOT_README.md`](src/visualization/PLOT_README.md) - Plotting module docs
- **Validation**: [`src/validation/VALIDATION_README.md`](src/validation/VALIDATION_README.md) - Data validation docs
- **Examples**: [`process_data.ipynb`](process_data.ipynb) - Jupyter notebook with usage patterns

## Troubleshooting

**Import errors?** Ensure virtual environment is active: `source venv/bin/activate`

**No data found?** Check paths in `config/sensor_config.yaml` and logs: `tail -f output/logs/<logfile>.log`

**Reprocess data**:
```python
pipeline = SensorPipeline(config, force=True)
pipeline.run_all(year=2024, month=10)
```

## Container Deployment

The pipeline runs in Docker or Podman without requiring a local Python install.

### 1. Configure Volumes

Edit `docker-compose.yaml` to mount your raw data directories. The container needs three volume types:

| Volume | Purpose | Mode |
|--------|---------|------|
| `./config:/app/config` | Sensor configuration | Read-only |
| `./output:/app/output` | Pipeline outputs (CSV, Parquet, logs, plots) | Read-write |
| `/host/path/to/data:/data/scd41` | Raw SCD41 sensor files | Read-only |
| `/host/path/to/data:/data/lgr` | Raw LGR sensor files | Read-only |

Example `docker-compose.yaml` volumes:
```yaml
volumes:
  - ./config:/app/config:ro
  - ./output:/app/output
  - /mnt/sensors/SCD41:/data/scd41:ro
  - /mnt/sensors/LGR:/data/lgr:ro
```

### 2. Update Config Paths

The `input_dir` paths in `config/sensor_config.yaml` must reference the **container-side** mount points, not host paths:

```yaml
sensors:
  - name: CO2_SCT1_2M
    input_dir: /data/scd41/CO2-SCT1-2M   # ← container path, not host path
    sensor_type: scd41
    # ...
  - name: LGR_30M
    input_dir: /data/lgr                   # ← container path
    sensor_type: lgr_csv
    # ...
```

### 3. Build and Run

**Docker:**
```bash
docker compose build
docker compose up        # foreground (see logs)
docker compose up -d     # detached
docker compose logs -f   # follow logs if detached
```

**Podman:**
```bash
podman-compose build
podman-compose up
```

The image uses a multi-stage Alpine build (~50 MB) for minimal disk usage.

### 4. Output

Results appear in `./output/` on the host (mounted volume). The pipeline creates subdirectories automatically:
- `output/sensors/` — per-sensor CSVs and Parquet
- `output/merged/` — merged datasets
- `output/validation/` — validation reports
- `output/logs/` — processing logs

### Interactive Container Session

To open a shell for debugging or running Jupyter inside the container:
```bash
docker compose run --rm --entrypoint /bin/sh smear-co2
# then inside the container:
python -m src.pipeline       # run pipeline
python -c "import src; ..."  # test imports
```

> **Note:** `setup.sh` is for local (non-container) installs only. The container installs dependencies directly via the Dockerfile.

## Requirements

- Python 3.10+
- 8 GB RAM minimum, 16 GB recommended (pandas loads large DataFrames day-by-day)
- Modern multi-core CPU (e.g. Intel Core i5/Ultra 5 or equivalent)
- ~500 MB disk space for dependencies, plus space for raw and processed data
- Dependencies installed via `requirements.txt`: pandas, numpy, pyarrow, matplotlib, seaborn

## Citation

```
Zorec, M. et al. (2026). SMEAR Estonia CO2 Sensor Processing Pipeline.
Version 0.2.0. GitHub: SMEAR-EE/SCD41_DATA
Dataset available at: [(DOI pending) 10.xxxx/zenodo.xxxxx]
```

## Version

**Current Release:** v0.2.0 (Stable)

## License

Software application licensed under the Apache License 2.0 (see [LICENSE](LICENSE) file).
Dataset licensed under CC BY 4.0, available on [Zenodo.org/#](https://zenodo.org/).