# SMEAR Estonia CO2 Sensor Processing

Fast, reproducible processing pipeline for SCD41 and LGR CO2 sensor data.

## 🚀 Quick Start (5 minutes)
```bash
# 1. Setup (one-time)
./setup.sh

# 2. Activate environment
source venv/bin/activate

# 3. Edit config
micro config/sensors.yaml

# 4. Run processing
jupyter notebook notebooks/process_data.ipynb
```

**That's it!** Processed data appears in `output/`.

---

## 📊 What This Does

- ✅ Processes 5 sensors (4x SCD41, 1x LGR reference)
- ✅ Resamples to 10-min intervals (time-synchronized)
- ✅ Tracks uptime + data quality (QC flags)
- ✅ Exports CSV + Parquet files
- ✅ Generates validation plots

---

## 📁 Where Things Go

| What | Where |
|------|-------|
| Your raw data | Configure in `config/sensors.yaml` |
| Processed CSVs | `output/individual/` |
| Monthly parquets | `output/parquet/` |
| Plots | `output/plots/` |
| Logs | `output/logs/` |

---

## 🔧 Configuration

Edit `config/sensors.yaml`:
```yaml
sensors:
  - name: CO2_SCT1_2M
    input_dir: /your/path/here  # ← EDIT THIS
    # ... (rest auto-configured)
```

---

## 📖 Documentation

- **Full structure:** See `PROJECT_STRUCTURE.md`
- **Module details:** See docstrings in `src/`
- **Examples:** See `notebooks/process_data.ipynb`

---

## 🐛 Troubleshooting

**Import errors?**
```bash
source venv/bin/activate  # Activate venv first!
```

**No data found?**
- Check paths in `config/sensors.yaml`
- Check logs: `tail -f output/logs/processing.log`

**Need to reprocess?**
```python
pipeline = SensorPipeline(config, force=True)
pipeline.run_all(year=2024, month=10)
```

---

## 🎨 Extending

Want to add custom plots or analysis?

1. Edit `src/visualization.py` (add methods to `SensorVisualizer`)
2. Call from notebook
3. Done!

See `PROJECT_STRUCTURE.md` for details.

---

## 📦 Requirements

- Python 3.10+
- ~500 MB disk space (for venv + processed data)
- Jupyter (auto-installed)

---

## 📝 Citation
```
Zorec, M. et al. (2025). Title TBD.
Dataset: [DOI pending]
```