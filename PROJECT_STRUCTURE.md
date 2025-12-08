# 📁 Project Structure

## Quick Navigation
```
SCD41_DATA/
│
├── 📜 setup.sh / setup.bat      ← START HERE (run once)
├── 📜 requirements.txt          ← Python dependencies
├── 📜 README.md                 ← Overview
├── 📜 PROJECT_STRUCTURE.md      ← THIS FILE (your map!)
│
├── 📁 config/
│   └── sensors.yaml             ← EDIT THIS with your paths
│
├── 📁 src/                      ← Core code (don't edit unless extending)
│   ├── __init__.py
│   ├── config.py                ← Loads sensors.yaml
│   ├── uptime.py                ← Uptime calculations
│   ├── processor.py             ← Day-level processing
│   ├── pipeline.py              ← Main orchestrator
│   ├── visualization.py         ← Plotting functions
│   └── parsers/
│       ├── __init__.py
│       ├── base_parser.py       ← Abstract parser interface
│       ├── scd41_parser.py      ← JSON parser (4 sensors)
│       └── lgr_parser.py        ← CSV parser (LGR reference)
│
├── 📁 notebooks/
│   └── process_data.ipynb       ← MAIN INTERFACE (use this!)
│
├── 📁 output/                   ← Generated data (gitignored)
│   ├── individual/              ← Per-sensor CSVs + uptime logs
│   ├── parquet/                 ← Monthly compressed files
│   ├── logs/                    ← Processing logs
│   └── plots/                   ← Generated figures
│
└── 📁 venv/                     ← Python virtual environment (auto-created)
```

---

## What Each File Does

### **YOU ONLY NEED TO TOUCH 2 FILES:**

1. **`config/sensors.yaml`** - Set your data paths
2. **`notebooks/process_data.ipynb`** - Run processing + plots

---

### Core Modules (src/)

| File | Purpose | When to Edit |
|------|---------|--------------|
| `config.py` | Loads YAML config | Never |
| `uptime.py` | Calculates sensor uptime | Only if new uptime modes needed |
| `processor.py` | Processes one day | Never |
| `pipeline.py` | Orchestrates full run | Never |
| `visualization.py` | Creates plots | **Add new plot functions here** |
| `parsers/scd41_parser.py` | Parses SCD41 JSON | Only if JSON format changes |
| `parsers/lgr_parser.py` | Parses LGR CSV | Only if LGR format changes |

---

## Workflow

### 1️⃣ First Time Setup
```bash
./setup.sh                    # Creates venv + installs packages
source venv/bin/activate      # Activate environment
```

### 2️⃣ Edit Configuration
```bash
nano config/sensors.yaml      # Set your data directories
```

### 3️⃣ Run Processing
```bash
jupyter notebook notebooks/process_data.ipynb
# OR
python -c "from src.pipeline import *; ..."
```

### 4️⃣ Check Outputs
```bash
ls -lh output/individual/     # Per-sensor CSVs
ls -lh output/parquet/        # Monthly compressed files
ls -lh output/plots/          # Figures
```

---

## Adding New Features

### Add a New Plot
```python
# Edit: src/visualization.py
class SensorVisualizer:
    def plot_my_fancy_analysis(self, ...):
        # Your code here
        pass
```

### Add a New Sensor Type
```python
# Create: src/parsers/my_sensor_parser.py
class MySensorParser(BaseSensorParser):
    # Implement abstract methods
    pass
```

### Change Processing Logic
```python
# Edit: src/processor.py
class DayProcessor:
    def _resample_10min(self, df):
        # Modify resampling logic
        pass
```

---

## Common Tasks

| Task | Command |
|------|---------|
| Activate venv | `source venv/bin/activate` |
| Process all data | See notebook Cell 3 |
| Process one month | See notebook Cell 4 |
| Force reprocess | See notebook Cell 5 |
| Generate plots | See notebook Cell 6 |
| Check logs | `tail -f output/logs/processing.log` |

---

## Files You Can Ignore

- `venv/` - Virtual environment (auto-generated)
- `output/` - Generated data (can delete and regenerate)
- `src/__pycache__/` - Python bytecode (auto-generated)
- `.ipynb_checkpoints/` - Jupyter temp files

---

## Getting Help

1. **Check logs:** `output/logs/processing.log`
2. **Test single sensor:** Edit notebook to process just `CO2_SCT1_2M`
3. **Dry run:** Set `force=False` to skip already-processed days