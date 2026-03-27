# SMEAR Estonia CO2 Sensor Processing

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/SMEAR-EE/SCD41_DATA/releases/tag/v0.3.0)
[![License](https://img.shields.io/badge/license-Apache_2.0-white.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Fast, light and reproducible post-processing pipeline for SCD41 and LGR CO2 raw sensor data at the Estonian Station for Measuring Ecosystem-Atmosphere Relations (SMEAR; [smear.emu.ee](https://smear.emu.ee/)).

> **Status:** v0.3.0 - Stable release with comprehensive validation suite and enhanced data quality reporting

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Configure sensors (copy template, then edit paths)
cp config/sensor_config.yaml config/sensors.yaml
# edit config/sensors.yaml  # Set your data paths

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

Copy the template and edit `config/sensors.yaml` to set input data paths:
```bash
cp config/sensor_config.yaml config/sensors.yaml
```
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
- **Container Deployment**: [`DOCKER.md`](DOCKER.md) - Docker/Podman setup, volume mounts, and configuration
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

**No data found?** Check paths in `config/sensors.yaml` and logs: `tail -f output/logs/<logfile>.log`

**Reprocess data**:
```python
pipeline = SensorPipeline(config, force=True)
pipeline.run_all(year=2024, month=10)
```

## Container Deployment

`docker compose up` or `podman-compose up`

See [`DOCKER.md`](DOCKER.md) for full setup instructions: volume mounts, config path notes, Docker/Podman commands, and output structure.

> Requires editing volume paths in `docker-compose.yaml` — see DOCKER.md for details.

## Requirements

- Python 3.10+
- 8 GB RAM minimum, 16 GB recommended (pandas loads large DataFrames day-by-day)
- Modern multi-core CPU (e.g. Intel Core i5/Ultra 5 or equivalent)
- ~500 MB disk space for dependencies, plus space for raw and processed data
- Dependencies installed via `requirements.txt`: pandas, numpy, pyarrow, matplotlib, seaborn

## Citation

```
Zorec, M. et al. (2026). SMEAR Estonia CO2 Sensor Processing Pipeline.
Version 0.3.0. GitHub: SMEAR-EE/SCD41_DATA
Dataset available at: 10.5281/zenodo.18984845
```

## Version

**Current Release:** v0.3.0 (Stable)

## License

- Software application licensed under the Apache License 2.0 (see [LICENSE](LICENSE) file).
- Dataset licensed under CC BY 4.0, available on [https://zenodo.org/uploads/18984845](http://doi.org/10.5281/zenodo.18984845).