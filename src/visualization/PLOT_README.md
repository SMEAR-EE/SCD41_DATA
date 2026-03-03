# Visualization Module

Modular plotting package for sensor data visualization with uptime, validation, and QC plots.

## Quick Start

```python
from visualization import generate_all_plots
generate_all_plots(config)  # Generate all plots at once
```

Or use individual plotters:

```python
from visualization import UptimePlots, ValidationPlots, QualityControlPlots

uptime = UptimePlots("plots/")
validation = ValidationPlots("plots/")
qc = QualityControlPlots("plots/")
```

## Available Plotters

### UptimePlots
- `plot_timeseries(csv, sensor)` - Time series with data availability
- `plot_heatmap(csv, sensor)` - Calendar heatmap showing gaps
- `plot_summary(csv_dict)` - Multi-sensor comparison

### ValidationPlots
- `plot_timeseries(data_csvs, start_date, end_date)` - Overlay multiple sensors
- `plot_scatter(reference_csv, test_csv, ref_name, test_name)` - Sensor vs reference
- `plot_difference(reference_csv, test_csv, ref_name, test_name)` - Bias analysis

### QualityControlPlots
- `plot_qc_summary(data_csv, sensor_name)` - QC flag distribution

## Example Usage

```python
# Uptime analysis
uptime.plot_timeseries("CO2_30M_A_uptime.csv", "CO2_30M_A")
uptime.plot_heatmap("CO2_30M_A_uptime.csv", "CO2_30M_A")

# Validation against reference
validation.plot_scatter("LGR_30M.csv", "CO2_30M_A.csv", "LGR", "SCD41_A")
validation.plot_difference("LGR_30M.csv", "CO2_30M_A.csv", "LGR", "SCD41_A")

# Quality control
qc.plot_qc_summary("CO2_30M_A.csv", "CO2_30M_A")
```

## Structure

```
visualization/
├── __init__.py              # Main entry point
├── base_plotter.py          # Shared styling and utilities
├── uptime_plots.py          # Uptime visualizations
├── validation_plots.py      # Sensor validation plots
├── quality_control.py       # QC analysis plots
├── taylor_diagram_custom.py # Taylor diagrams (TaylorDiagram + TaylorPlotter)
```

## Notes

- All plots except Taylor share consistent styling via `base_plotter.py`
- Plots auto-save to configured output directory