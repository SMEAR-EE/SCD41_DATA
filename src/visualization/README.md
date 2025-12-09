# Visualization Module: Quick Reference

# Visualization Module Refactoring - Complete Package

## 📦 What You Got

Your monolithic 700-line `visualization.py` has been refactored into a clean, modular package with comprehensive documentation.

## 📂 Package Contents

```
outputs/
├── visualization/                     ← THE MAIN PACKAGE
│   ├── __init__.py         (117 lines) - Package exports & convenience function
│   ├── base.py              (56 lines) - Shared matplotlib configuration
│   ├── uptime.py           (182 lines) - Uptime analysis plots
│   ├── validation.py       (229 lines) - CO2 comparison/validation plots
│   ├── quality_control.py   (73 lines) - QC flag analysis
│   ├── taylor.py           (124 lines) - Taylor diagrams (broken, isolated)
│   └── README.md                       - Package documentation
│
└── Documentation/
    ├── QUICK_REFERENCE.md              - Start here! Quick usage guide
    ├── REFACTORING_SUMMARY.md          - Detailed migration guide
    ├── BEFORE_AFTER_COMPARISON.md      - Side-by-side comparison
    └── INDEX.md                        - This file
```

## 🚀 Quick Start (30 seconds)

1. **Copy the package to your project:**
   ```bash
   cp -r visualization/ /path/to/your/project/
   ```

2. **Test that it works:**
   ```python
   from visualization import generate_all_plots
   generate_all_plots(config)  # Should work identically to before!
   ```

3. **Done!** Everything should work exactly as before.

## 📖 Documentation Guide

### Start Here
**[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - 5 minute read
- Quick installation
- Usage examples
- Common patterns
- Method summary
- Troubleshooting

### Deep Dive
**[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - 10 minute read
- What changed and why
- New structure benefits
- API changes (old vs new)
- Migration path
- Testing recommendations
- Future enhancements

### Comparison
**[BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md)** - 8 minute read
- Visual structure comparison
- Import comparison
- Code organization
- Extensibility comparison
- Real-world scenarios
- Summary table

### Package Documentation
**[visualization/README.md](visualization/README.md)** - 7 minute read
- Module overview
- Usage examples
- Benefits of modular structure
- Future plot ideas
- Migration notes

## 🎯 Key Benefits

| What | Before | After |
|------|--------|-------|
| **File size** | 1 file (700 lines) | 6 modules (56-229 lines each) |
| **Maintainability** | Scroll through 700 lines | Open relevant module |
| **Broken code** | Mixed with working code | Isolated in `taylor.py` |
| **Adding features** | Edit big file | Create new module |
| **Risk** | Break unrelated code | Isolated changes |
| **Imports** | Import everything | Import what you need |

## 🔧 What's Different?

### The Good News
✅ **Convenience function works identically** - `generate_all_plots(config)` works as before  
✅ **Same functionality** - All working plots preserved  
✅ **Better organized** - Easier to find and modify code  
✅ **Room to grow** - Easy to add new plot types  
✅ **Broken code isolated** - Taylor diagram in separate file

### What Changed
- Monolithic file → Modular package
- `SensorVisualizer` → Multiple focused classes (`UptimePlots`, `ValidationPlots`, etc.)
- Method names simplified (context from class name)
- Taylor diagram isolated with warnings

## 📊 Statistics

```
Original:
  visualization.py:     700 lines (everything)

Refactored:
  base.py:               56 lines (foundation)
  uptime.py:            182 lines (uptime plots)
  validation.py:        229 lines (validation plots)
  quality_control.py:    73 lines (QC plots)
  taylor.py:            124 lines (broken, isolated)
  __init__.py:          117 lines (convenience + exports)
  ─────────────────────────────────
  Total:                781 lines (includes extra docs)
```

## 🛠️ Usage Examples

### Example 1: Use convenience function (no changes needed)
```python
from visualization import generate_all_plots

generate_all_plots(config)  # Works identically!
```

### Example 2: Use individual plotters (more control)
```python
from visualization import UptimePlots, ValidationPlots

uptime = UptimePlots("plots/")
uptime.plot_timeseries("data/sensor_uptime.csv", "CO2_30M_1")

validation = ValidationPlots("plots/")
validation.plot_scatter("data/lgr.csv", "data/scd41.csv", "LGR", "SCD41")
```

### Example 3: Generate specific plots only
```python
from visualization import ValidationPlots

validation = ValidationPlots("custom_plots/")

# Only validation plots, custom date range
validation.plot_timeseries(
    data_csvs={"LGR": "lgr.csv", "SCD41": "scd41.csv"},
    start_date="2024-06-01",
    end_date="2024-08-31"
)
```

## 🔍 Find What You Need

| I want to... | Read this |
|--------------|-----------|
| **Get started quickly** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **Understand the changes** | [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) |
| **See before/after examples** | [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md) |
| **Learn the new API** | [visualization/README.md](visualization/README.md) |
| **Copy usage examples** | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| **Migrate existing code** | [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) |

## ⚠️ Known Issues

**Taylor Diagram (taylor.py)**
- Status: BROKEN (isolated in separate module)
- Impact: Can skip this plot for now
- Fix: Later when you have time, or use `skill_metrics` package
- Safety: Won't affect other plots (isolated)

## 🚧 Future Enhancements

Easy to add (modular structure makes this simple):

1. **Diurnal cycle plots** → Create `visualization/diurnal.py`
2. **Vertical gradient analysis** → Add to `validation.py`
3. **Meteorological correlations** → Create `visualization/meteorology.py`
4. **Spectral analysis (FFT)** → Create `visualization/spectral.py`
5. **Advanced skill scores** → Fix/replace `taylor.py`

Each can be developed independently!

## ✅ Migration Checklist

1. [ ] Copy `visualization/` directory to your project
2. [ ] Remove old `visualization.py` file
3. [ ] Test imports: `from visualization import generate_all_plots`
4. [ ] Run your pipeline: `generate_all_plots(config)`
5. [ ] Verify plots are generated correctly
6. [ ] (Optional) Update code to use individual plotters
7. [ ] (Optional) Fix or replace Taylor diagram later

## 🎓 Learning Path

**If you have 5 minutes:**
Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) and start using it.

**If you have 15 minutes:**
Read [QUICK_REFERENCE.md](QUICK_REFERENCE.md) + [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

**If you have 30 minutes:**
Read everything! You'll understand the full design and be able to extend it easily.

## 💡 Pro Tips

1. **Keep using `generate_all_plots(config)`** - It's the easiest way
2. **Use individual plotters** when you need custom analysis
3. **Don't delete old `visualization.py` yet** - Keep as backup during testing
4. **Fix Taylor diagram later** - It's isolated, won't affect anything else
5. **Add new plot types as new modules** - Don't edit existing files

## 📞 Need Help?

The documentation is comprehensive, but if you have questions:
1. Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common patterns
2. Check [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) for migration details
3. Check module docstrings in the code itself
4. The code is well-commented and follows consistent patterns

## 🎉 Summary

You now have a clean, modular, maintainable visualization package with:
- ✅ All working functionality preserved
- ✅ Broken code isolated
- ✅ Room to grow
- ✅ Comprehensive documentation
- ✅ Backwards compatible convenience function

**Just copy the `visualization/` directory to your project and you're done!**

---

*Generated: December 2025*  
*Original file: visualization.py (700 lines)*  
*Refactored: visualization/ package (6 modules, 781 lines including extra docs)*


## Installation

Just replace your old `visualization.py` file with the new `visualization/` directory.

```bash
# Your project structure should look like:
your_project/
├── config.py
├── pipeline.py
├── visualization/          ← New package (directory)
│   ├── __init__.py
│   ├── base.py
│   ├── uptime.py
│   ├── validation.py
│   ├── quality_control.py
│   └── taylor.py
└── data/
```

## Quick Start

### Option 1: Use the convenience function (EASIEST)

```python
from visualization import generate_all_plots

# Generate all standard plots
generate_all_plots(config)
```

**This works identically to before!** No migration needed.

### Option 2: Use individual plotters (MORE CONTROL)

```python
from visualization import UptimePlots, ValidationPlots, QualityControlPlots

# Create plotters
uptime = UptimePlots(output_dir="plots/")
validation = ValidationPlots(output_dir="plots/")
qc = QualityControlPlots(output_dir="plots/")

# Generate specific plots
uptime.plot_timeseries("data/sensor_uptime.csv", "CO2_30M_1")
validation.plot_scatter("data/lgr.csv", "data/scd41.csv", "LGR", "SCD41")
qc.plot_qc_summary("data/sensor_10min.csv", "CO2_30M_1")
```

## Available Plotters

### UptimePlots
```python
from visualization import UptimePlots

uptime = UptimePlots(output_dir)

# Daily uptime timeseries
uptime.plot_timeseries(
    uptime_csv=Path("sensor_uptime.csv"),
    sensor_name="CO2_30M_1",
    save=True
)

# Monthly heatmap
uptime.plot_heatmap(
    uptime_csv=Path("sensor_uptime.csv"),
    sensor_name="CO2_30M_1",
    save=True
)

# Multi-sensor summary
uptime.plot_summary(
    uptime_csvs={
        "CO2_30M_1": Path("co2_1_uptime.csv"),
        "CO2_30M_2": Path("co2_2_uptime.csv")
    },
    save=True
)
```

### ValidationPlots
```python
from visualization import ValidationPlots

validation = ValidationPlots(output_dir)

# CO2 timeseries comparison
validation.plot_timeseries(
    data_csvs={
        "LGR": Path("lgr_10min.csv"),
        "SCD41": Path("scd41_10min.csv")
    },
    start_date="2024-01-01",  # Optional
    end_date="2024-12-31",    # Optional
    save=True
)

# Scatter plot (test vs reference)
validation.plot_scatter(
    reference_csv=Path("lgr_10min.csv"),
    test_csv=Path("scd41_10min.csv"),
    reference_name="LGR",
    test_name="SCD41",
    save=True
)

# Difference analysis (test - reference)
validation.plot_difference(
    reference_csv=Path("lgr_10min.csv"),
    test_csv=Path("scd41_10min.csv"),
    reference_name="LGR",
    test_name="SCD41",
    save=True
)
```

### QualityControlPlots
```python
from visualization import QualityControlPlots

qc = QualityControlPlots(output_dir)

# QC flag distribution
qc.plot_qc_summary(
    data_csv=Path("sensor_10min.csv"),
    sensor_name="CO2_30M_1",
    save=True
)
```

### TaylorDiagram (WARNING: BROKEN)
```python
from visualization import TaylorDiagram

taylor = TaylorDiagram(output_dir)

# Multi-sensor Taylor diagram
taylor.plot(
    reference_csv=Path("lgr_10min.csv"),
    test_csvs={
        "SCD41_1": Path("scd41_1_10min.csv"),
        "SCD41_2": Path("scd41_2_10min.csv")
    },
    reference_name="LGR",
    save=True
)
```
**Note:** This needs fixing! Consider using `skill_metrics` package instead.

## Common Patterns

### Generate all plots for one sensor
```python
from visualization import UptimePlots, ValidationPlots, QualityControlPlots

sensor = "CO2_30M_1"
output_dir = "plots/"

# Uptime
uptime = UptimePlots(output_dir)
uptime.plot_timeseries(f"data/{sensor}_uptime.csv", sensor)
uptime.plot_heatmap(f"data/{sensor}_uptime.csv", sensor)

# QC
qc = QualityControlPlots(output_dir)
qc.plot_qc_summary(f"data/{sensor}_10min.csv", sensor)

# Validation
validation = ValidationPlots(output_dir)
validation.plot_scatter(
    "data/LGR_30M_10min.csv",
    f"data/{sensor}_10min.csv",
    "LGR",
    sensor
)
```

### Compare multiple sensors
```python
from visualization import UptimePlots, ValidationPlots

sensors = ["CO2_30M_1", "CO2_30M_2", "CO2_30M_3"]
output_dir = "plots/"

# Uptime comparison
uptime = UptimePlots(output_dir)
uptime_csvs = {s: f"data/{s}_uptime.csv" for s in sensors}
uptime.plot_summary(uptime_csvs)

# CO2 timeseries comparison
validation = ValidationPlots(output_dir)
data_csvs = {s: f"data/{s}_10min.csv" for s in sensors}
validation.plot_timeseries(data_csvs)
```

## Method Summary

| Module | Method | Purpose |
|--------|--------|---------|
| `UptimePlots` | `plot_timeseries()` | Daily uptime over time |
| `UptimePlots` | `plot_heatmap()` | Monthly uptime heatmap |
| `UptimePlots` | `plot_summary()` | Multi-sensor comparison |
| `ValidationPlots` | `plot_timeseries()` | Multi-sensor CO2 timeseries |
| `ValidationPlots` | `plot_scatter()` | Reference vs test scatter |
| `ValidationPlots` | `plot_difference()` | Difference analysis |
| `QualityControlPlots` | `plot_qc_summary()` | QC flag distribution |
| `TaylorDiagram` | `plot()` | Taylor diagram (BROKEN) |

## Tips

1. **Use convenience function for standard workflow:**
   ```python
   generate_all_plots(config)
   ```

2. **Use individual plotters for custom analysis:**
   ```python
   validation = ValidationPlots("custom_plots/")
   validation.plot_scatter(..., start_date="2024-06-01")
   ```

3. **Disable auto-save to preview plots:**
   ```python
   fig = uptime.plot_timeseries(..., save=False)
   plt.show()
   ```

4. **All plotters inherit from `BasePlotter`:**
   - Consistent matplotlib styling
   - Automatic output directory creation
   - Logging built-in

## Troubleshooting

**Q: ImportError: cannot import name 'UptimePlots'**  
A: Make sure you have the `visualization/` directory (not file!) with `__init__.py`

**Q: Plots look different than before**  
A: Same matplotlib configuration, should look identical. Check your data.

**Q: Taylor diagram not working**  
A: Known issue! It's isolated in `taylor.py`. Fix later or use `skill_metrics` package.

**Q: Where are my plots saved?**  
A: Check the `output_dir` you passed to the plotter constructor.

## Migration Checklist

- [ ] Replace `visualization.py` with `visualization/` directory
- [ ] Test imports: `from visualization import generate_all_plots`
- [ ] Run `generate_all_plots(config)` to verify it works
- [ ] (Optional) Update code to use individual plotters
- [ ] (Optional) Fix or replace Taylor diagram in `taylor.py`

## Need Help?

Check the full documentation:
- `README.md` - Module overview
- `REFACTORING_SUMMARY.md` - Detailed migration guide
- `BEFORE_AFTER_COMPARISON.md` - Side-by-side comparison
