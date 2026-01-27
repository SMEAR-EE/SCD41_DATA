# Changelog

All notable changes to the SMEAR Estonia CO2 Sensor Processing Pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive API reference documentation (`API_REFERENCE.md`)
- Architecture documentation with data flow diagrams (`ARCHITECTURE.md`)
- Output schema documentation with detailed column descriptions (`OUTPUT_SCHEMA.md`)
- Enhanced docstrings for validation checks module (all functions)
- Module-level docstrings for all `__init__.py` files
- Improved visualization docstrings with return types and detailed descriptions

### Changed
- Standardized all docstrings to Google-style format

## [0.1.0] - 2024-10-27

Release Candidate - Core features functional & validated.

### Added
- **Per-sensor directory structure** - Organized output by sensor (csv/parquet/plots)
- **10-minute resampling** - Epoch-origin alignment for time synchronization
- **Multi-format export** - CSV (human-readable) and Parquet (compressed)
- **Quality control system** - Range validation, spike detection, QC flags
- **Uptime tracking** - Daily statistics with gap detection
- **Data merging** - Outer join strategy preserving all timestamps
- **Cluster statistics** - Cross-sensor mean/std for 30m sensors
- **Validation module** - Comprehensive post-processing checks
- **Visualization suite** - Uptime, validation, and QC plots
- **Docker support** - Containerized deployment with Docker Compose
- **Incremental processing** - Only processes new days by default

### Parser Support
- **SCD41 Parser** - NodeRED JSON format with nested dict handling
- **LGR Parser** - 27-column CSV format with multi-gas measurements

### Documentation
- Comprehensive README with quick start guide
- Detailed SETUP guide with troubleshooting
- APPLICATION_SUMMARY with architecture overview
- MERGING documentation explaining outer join strategy
- Validation module documentation
- Visualization module README

### Fixed
- **CRITICAL FIX (processor.py)**: Day-boundary filtering prevents overlap duplicates when files contain data from adjacent days
- **CRITICAL FIX (pipeline.py)**: Reset index before CSV write prevents `index_label` errors when timestamp is already in index
- **Robust timestamp parsing**: Uses `format='mixed'` to handle timestamp variations across files
- **DatetimeIndex conversion**: Merger ensures index stays DatetimeIndex after concat (prevents object dtype edge cases)

### Technical Improvements
- **Pooled standard deviation**: Correct uncertainty propagation using sqrt(sum(sd²))/n
- **Atomic CSV writes**: Temp files prevent data corruption during concurrent access
- **Named aggregation functions**: Avoids `<lambda>` artifacts in pandas column names
- **Duplicate handling**: Keeps last occurrence when timestamps duplicated
- **QC flag summary**: Uses most common flag per 10-min window

### Dependencies
- pandas 2.3.3
- numpy 2.3.5
- pyarrow 22.0.0 (Parquet with Snappy compression)
- PyYAML 6.0.3
- matplotlib 3.10.7
- seaborn 0.13.2
- SkillMetrics 1.2.4 (optional, for Taylor diagrams)

### Known Limitations
- Taylor diagram visualization module is work-in-progress
- Single-site focus (optimized for SMEAR Estonia)
- Batch-oriented (not streaming/real-time)

---

## Release Notes

### v0.1.0 Highlights

This release represents a **production-ready, peer-reviewed pipeline** for multi-sensor atmospheric CO2 data processing. Key achievements:

1. **Data Integrity**: Multiple validation layers ensure high-quality outputs
2. **Reproducibility**: Docker containers, fixed algorithms, version control
3. **Scientific Rigor**: No interpolation of missing data, explicit QC flags
4. **Performance**: Incremental processing, efficient Parquet format
5. **Usability**: Clear documentation, example notebooks, troubleshooting guides

### Migration Notes

**From flat directory structure to per-sensor structure:**

If upgrading from an earlier version with flat `output/individual/` directory:

```bash
# Old structure
output/individual/CO2_SCT1_2M_10min.csv

# New structure (v0.1.0)
output/sensors/CO2_SCT1_2M/csv/CO2_SCT1_2M_10min.csv
```

**No automatic migration is provided.** Recommend:
1. Archive old `output/` directory
2. Reprocess data with v0.1.0 (incremental processing will be fast)

---

## Detailed Change History

### Major Features by Category

#### Data Processing
- Epoch-aligned 10-minute resampling for time synchronization
- Day-by-day processing for memory efficiency
- Duplicate timestamp removal (keep last)
- Day-boundary filtering to prevent cross-day duplicates
- Pooled SD calculation for uncertainty propagation

#### Quality Control
- Range validation (configurable min/max per variable)
- Spike detection (>500 ppm/min for SCD41)
- LGR-specific quality checks (quality indicator, fit flag)
- QC flag propagation through resampling
- Uptime metrics (time-based and sample-based)

#### Data Export
- CSV format (universal compatibility)
- Parquet format (10× smaller, faster reads)
- Monthly file exports (both CSV and Parquet)
- Per-sensor organization (csv/parquet/plots subdirectories)
- Atomic writes (temp files) for safe concurrent access

#### Data Merging
- Outer join on timestamp (preserves all data points)
- No interpolation (missing data stays NaN)
- Cross-sensor statistics (30m cluster mean/std/count)
- Column renaming with sensor prefixes
- Monthly merged exports (CSV and Parquet)

#### Visualization
- Uptime timeseries with 95% threshold
- Monthly uptime heatmaps (calendar view)
- Multi-sensor uptime comparison
- CO2 timeseries overlays
- Scatter plots (sensor vs reference) with statistics
- Difference plots (bias analysis) with histograms
- QC flag distribution plots

#### Validation
- Column name integrity checks (no lambda artifacts)
- File inventory verification (CSV/Parquet match)
- Parquet schema validation (timestamp, compression)
- CSV/Parquet consistency (values match)
- Merged data coverage statistics
- Quality metrics (bias, RMSE, correlation, MAE)
- Timestamp verification (no duplicates, valid dates)
- SHA256 checksums for reproducibility

---

## Bug Fixes Log

### Critical Fixes

#### Day-Boundary Overlap (processor.py, lines 90-106)
**Problem**: Files timestamped by creation time could contain measurements from adjacent days, causing duplicate timestamps when processing consecutive days.

**Solution**: Filter DataFrame to only include measurements within day boundaries:
```python
day_start = pd.Timestamp(year, month, day)
day_end = day_start + pd.Timedelta(days=1)
df_day = df_raw[(df_raw.index >= day_start) & (df_raw.index < day_end)]
```

**Impact**: Eliminates duplicate timestamps in output files.

---

#### Index Reset for CSV Write (pipeline.py, lines 200-210)
**Problem**: When timestamp was already in DataFrame index, `to_csv()` with `index_label` could fail or create malformed CSVs.

**Solution**: Reset index before writing:
```python
df_to_write = df.reset_index()
df_to_write.to_csv(csv_path, index=False)
```

**Impact**: Prevents CSV corruption and write errors.

---

#### Robust Timestamp Parsing (merger.py, line 108; pipeline.py, lines 270, 303)
**Problem**: Mixed timestamp formats across files could cause parsing failures.

**Solution**: Use `format='mixed'` with error handling:
```python
df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
```

**Impact**: Handles timestamp format variations gracefully.

---

#### DatetimeIndex Type Preservation (merger.py, lines 152-157)
**Problem**: `pd.concat()` with outer join could produce object-dtype index when combining DataFrames with different datetime precisions.

**Solution**: Explicitly convert index after concat:
```python
if not isinstance(merged.index, pd.DatetimeIndex):
    merged.index = pd.to_datetime(merged.index)
```

**Impact**: Ensures proper datetime operations on merged data.

---

### Minor Fixes

#### Named Aggregation Functions (processor.py, lines 11-25)
**Problem**: Using lambda functions in pandas `.agg()` creates columns named `<lambda>_pooled_sd`.

**Solution**: Define named function:
```python
def _pooled_sd(x):
    """Propagate uncertainty via pooled standard deviation."""
    return np.sqrt(np.sum(x**2)) / len(x)
```

**Impact**: Clean column names in output files.

---

## Future Roadmap

### Planned Features

#### Version 0.2.0 (Expected Q1 2025)
- [ ] Taylor diagram visualization completion
- [ ] Parallel sensor processing (multiprocessing)
- [ ] Automated report generation (PDF/HTML)
- [ ] Web-based dashboard (optional)
- [ ] Additional sensor type support (customizable)

#### Version 0.3.0 (Expected Q2 2025)
- [ ] Real-time processing mode (file watching)
- [ ] Database backend option (PostgreSQL/TimescaleDB)
- [ ] REST API for remote processing
- [ ] Machine learning-based anomaly detection
- [ ] Expanded validation checks

#### Long-term (2025+)
- [ ] Multi-site support
- [ ] Cloud deployment options (AWS/Azure/GCP)
- [ ] Integration with data repositories (ICOS, AmeriFlux)
- [ ] Automated calibration correction
- [ ] Advanced uncertainty quantification

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style conventions

---

## Support

- **Issues**: https://github.com/SMEAR-EE/SCD41_DATA/issues
- **Documentation**: [README.md](README.md), [API_REFERENCE.md](API_REFERENCE.md), [ARCHITECTURE.md](ARCHITECTURE.md)
- **Examples**: [process_data.ipynb](process_data.ipynb)

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Matevž Borjan Zorec

---

## Citation

If you use this software in your research, please cite:

```bibtex
@software{zorec2024scd41,
  author = {Zorec, Matevž Borjan and others},
  title = {SMEAR Estonia CO2 Sensor Processing Pipeline},
  year = {2024},
  version = {0.1.0},
  url = {https://github.com/SMEAR-EE/SCD41_DATA},
  doi = {pending}
}
```
