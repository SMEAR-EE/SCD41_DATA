# SMEAR Estonia CO2 Sensor Processing

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/SMEAR-EE/SCD41_DATA/releases/tag/v0.1.0)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Fast, light and reproducible processing pipeline for SCD41 and LGR CO2 sensor data at the SMEAR Estonia atmospheric research station.

> **Status:** Release Candidate v0.1.0 - Core features are functional and validated. Future work will focus on refactoring and enhancements.

## 🚀 Quick Start

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

## 📊 What It Does

Processes 5 CO2 sensors (4× SCD41, 1× LGR reference) with:
- **Time-synchronized resampling** to 10-min intervals (epoch-aligned)
- **Quality control** tracking uptime and data quality flags
- **Multiple outputs** CSV and Parquet formats
- **Visualization** uptime, validation, and QC plots

## 📁 Output Structure

| Output | Location |
|--------|----------|
| Processed CSVs | `output/individual/` |
| Monthly Parquet | `output/parquet/` |
| Plots | `output/plots/` |
| Logs | `output/logs/` |

## 🔧 Configuration

Edit `config/sensors.yaml` to set input data paths:
```yaml
sensors:
  - name: CO2_SCT1_2M
    input_dir: /path/to/your/data  # ← Change this
    sensor_type: scd41
    # Other settings auto-configured
```

## 📖 Documentation

- **Release notes**: See [`CHANGELOG.md`](CHANGELOG.md) for version history and release notes
- **Release checklist**: See [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) for release preparation steps
- **Detailed overview**: See [`APPLICATION_SUMMARY.md`](APPLICATION_SUMMARY.md) for architecture, features, and technical details
- **Setup guide**: See [`SETUP.md`](SETUP.md) for installation and configuration
- **Data merging**: See [`MERGING.md`](MERGING.md) for information on how sensor data is merged
- **Visualization**: See [`src/visualization/README.md`](src/visualization/README.md) for plotting module
- **Examples**: See [`process_data.ipynb`](process_data.ipynb) for usage patterns

## 🐛 Troubleshooting

**Import errors**: Ensure virtual environment is active: `source venv/bin/activate`

**No data found**: Check paths in `config/sensors.yaml` and logs: `tail -f output/logs/processing.log`

**Reprocess data**:
```python
pipeline = SensorPipeline(config, force=True)
pipeline.run_all(year=2024, month=10)
```

## 🐳 Docker Deployment

```bash
docker-compose up
```

Requires editing volume paths in `docker-compose.yaml`.

## 📦 Requirements

- Python 3.10+
- ~500 MB disk space
- Dependencies: pandas, numpy, pyarrow, matplotlib, seaborn

## 📝 Citation

```
Zorec, M. et al. (2025). SMEAR Estonia CO2 Sensor Processing Pipeline.
Version 0.1.0. GitHub: SMEAR-EE/SCD41_DATA
Dataset: [DOI pending]
```

## 📦 Version

**Current Release:** v0.1.0 (Release Candidate)  
See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.