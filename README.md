# SMEAR Estonia CO2 Sensor Processing

Fast, light and reproducible processing pipeline for SCD41 and LGR CO2 sensor data at the SMEAR Estonia atmospheric research station.

## 🚀 Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Configure sensors
edit config/sensors.yaml  # Set your data paths

# 4. Run processing
jupyter notebook testing/process_data.ipynb
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

- **Detailed overview**: See [`APPLICATION_SUMMARY.md`](APPLICATION_SUMMARY.md) for architecture, features, and technical details
- **Visualization**: See [`src/visualization/README.md`](src/visualization/README.md) for plotting module
- **Examples**: See [`testing/process_data.ipynb`](testing/process_data.ipynb) for usage patterns

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
Zorec, M. et al. (2025). Title TBD.
Dataset: [DOI pending]
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file.