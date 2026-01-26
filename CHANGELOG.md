# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-26

### Initial Release Candidate

This is the first release candidate for the SMEAR Estonia CO2 Sensor Processing Pipeline.

#### Added
- **Multi-sensor data processing** for 4x SCD41 + 1x LGR CO2 sensors
- **Time synchronization** with 10-minute interval resampling (epoch-aligned)
- **Quality control system** with uptime tracking and data validation
- **Multiple output formats** (CSV and Parquet with Snappy compression)
- **Comprehensive visualization** module with uptime, validation, and QC plots
- **Data merging** capability with outer join strategy
- **Robust parsers** for SCD41 (NodeRED JSON) and LGR (CSV) formats
- **Docker support** with Dockerfile and docker-compose.yaml
- **Configuration management** via YAML files
- **Incremental processing** with atomic writes and safe CSV appending
- **Detailed logging** with structured output to files and console
- **Extensive documentation** including:
  - README.md (Quick start guide)
  - APPLICATION_SUMMARY.md (Technical overview)
  - SETUP.md (Installation guide)
  - MERGING.md (Data merging documentation)
  - Visualization module README

#### Features in Detail

**Data Processing:**
- Automatic duplicate removal
- Gap detection and analysis
- Range validation with configurable thresholds
- Uncertainty propagation for standard deviation
- QC flag summary (most common flag per window)

**Output Management:**
- Per-sensor CSV files in `output/individual/`
- Monthly Parquet files in `output/parquet/`
- Plots in `output/plots/`
- Processing logs in `output/logs/`
- Uptime logs with daily statistics

**Visualization:**
- Time series plots with data availability
- Calendar heatmaps for gap identification
- Multi-sensor comparison plots
- Scatter plots (sensor vs. reference)
- Difference plots (bias analysis)
- QC flag distribution plots

**Quality Assurance:**
- Validation receipt generation with checksums
- CSV/Parquet data integrity checks
- Configurable quality control flags
- Graceful error handling per sensor

#### Known Limitations
- **Taylor diagram module** (`taylor_plots.py`) is work-in-progress and not yet fully functional
- **Single-site focus**: Optimized for SMEAR Estonia station
- **File format specificity**: Parsers designed for NodeRED JSON and LGR CSV formats
- **No real-time processing**: Batch-oriented, not streaming

#### Performance
- Memory efficient: Processes data day-by-day
- Incremental processing: Only processes new data by default
- Fast startup: ~5 minutes from clone to first results
- Efficient I/O: Parquet compression reduces storage footprint

#### Requirements
- Python 3.10+
- ~500 MB disk space for dependencies
- Core dependencies: pandas 2.3.3, numpy 2.3.5, pyarrow 22.0.0, PyYAML 6.0.3
- Visualization: matplotlib 3.10.7, seaborn 0.13.2
- Optional: SkillMetrics 1.2.4 (for future Taylor diagram support)

#### Documentation
All documentation is complete and peer-reviewed for initial release.

### Future Work (Post v0.1.0)

Future releases may include:
- Directory structure refactoring and improved output organization
- Complete Taylor diagram implementation
- Additional validation metrics and visualization tools
- Multi-site configuration support
- Performance optimizations

---

## Release Notes

### How to Use This Release

1. **Setup** (one-time):
   ```bash
   git clone https://github.com/SMEAR-EE/SCD41_DATA
   cd SCD41_DATA
   ./setup.sh
   ```

2. **Configure**:
   ```bash
   edit config/sensors.yaml  # Set your data paths
   ```

3. **Run** (local interaction or within bash script):
   ```bash
   source activate.sh
   jupyter notebook process_data.ipynb
   ```

### Docker Deployment

```bash
docker-compose up
```

Requires editing volume paths in `docker-compose.yaml`.

### Citation

If you use this software in your research, please cite:

```
Zorec, M. et al. (2025). SMEAR Estonia CO2 Sensor Processing Pipeline.
Version 0.1.0. GitHub: SMEAR-EE/SCD41_DATA
Note: Citation format and DOI will be updated upon article publication and Zenodo release.
```

---

[0.1.0]: https://github.com/SMEAR-EE/SCD41_DATA/releases/tag/v0.1.0
