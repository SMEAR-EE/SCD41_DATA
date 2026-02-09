# SMEAR Estonia CO2 Sensor Processing

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/SMEAR-EE/SCD41_DATA/releases/tag/v0.1.0)
[![License](https://img.shields.io/badge/license-MIT-white.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Fast, light and reproducible post-processing pipeline for SCD41 and LGR CO2 raw sensor data at the Estonian Station for Measuring Ecosystem-Atmosphere Relations (SMEAR; [smear.emu.ee](https://smear.emu.ee/)).

> **Status:** Release Candidate v0.1.0 - most features functional and validated. Future work: test and refactor

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Configure sensors
edit config/sensors.yaml  # Set your data paths

# 4. Run processing
jupyter notebook process_data.ipynb
```

Processed data appears in `output/`.

## What It Does

Processes many sensors (4x SCD41, 1x LGR reference) with:
- **Time-synced resampling** to 10-min intervals (epoch-aligned)
- **Quality control** tracking uptime, data quality flags, validation report
- **Multi-out** CSV and Parquet formats
- **Visuals** uptime, validation, and QC plots

## Output Structure

| Output | Location |
|--------|----------|
| Processed CSVs | `output/individual/` |
| Monthly Parquet | `output/parquet/` |
| Plots | `output/plots/` |
| Logs | `output/logs/` |

## Configuration

Edit `config/sensors.yaml` to set input data paths:
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
- **Application Summary**: [`APPLICATION_SUMMARY.md`](APPLICATION_SUMMARY.md) - Overview of features and research context
- **Data Merging**: [`MERGING.md`](MERGING.md) - Information on sensor data merging
- **Visualization**: [`src/visualization/README.md`](src/visualization/README.md) - Plotting module docs
- **Validation**: [`src/validation/VALIDATION_README.md`](src/validation/VALIDATION_README.md) - Data validation docs
- **Examples**: [`process_data.ipynb`](process_data.ipynb) - Jupyter notebook with usage patterns

## Troubleshooting

**Import errors**: Ensure virtual environment is active: `source venv/bin/activate`

**No data found**: Check paths in `config/sensors.yaml` and logs: `tail -f output/logs/processing.log`

**Reprocess data**:
```python
pipeline = SensorPipeline(config, force=True)
pipeline.run_all(year=2024, month=10)
```

## Docker Deployment

```bash
docker-compose up
```

Requires editing volume paths in `docker-compose.yaml`.

## Requirements

- Python 3.10+
- ~500 MB disk space
- Dependencies: pandas, numpy, pyarrow, matplotlib, seaborn

## Citation

```
Zorec, M. et al. (2025). SMEAR Estonia CO2 Sensor Processing Pipeline.
Version 0.1.0. GitHub: SMEAR-EE/SCD41_DATA
Dataset: [DOI pending]
```

## Version

**Current Release:** v0.1.0 (Release Candidate)

## License

MIT License - see [LICENSE](LICENSE) file.