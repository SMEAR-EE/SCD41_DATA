# Visualization Module – Minimal README

## Overview

Modular plotting package replacing the former monolithic `visualization.py`.
Provides uptime, validation, and QC plots with an optional (broken) Taylor diagram.

## Structure

```
visualization/
├── __init__.py
├── base.py
├── uptime.py
├── validation.py
├── quality_control.py
└── taylor.py
```

## Quick Start

Use the convenience function:

```python
from visualization import generate_all_plots
generate_all_plots(config)
```

Or instantiate plotters:

```python
from visualization import UptimePlots, ValidationPlots, QualityControlPlots

uptime = UptimePlots("plots/")
validation = ValidationPlots("plots/")
qc = QualityControlPlots("plots/")
```

## Main Plotters

### UptimePlots

* `plot_timeseries(csv, sensor)`
* `plot_heatmap(csv, sensor)`
* `plot_summary(csv_dict)`

### ValidationPlots

* `plot_timeseries(data_csvs, start_date=None, end_date=None)`
* `plot_scatter(reference_csv, test_csv, reference_name, test_name)`
* `plot_difference(reference_csv, test_csv, reference_name, test_name)`

### QualityControlPlots

* `plot_qc_summary(data_csv, sensor_name)`

### TaylorDiagram (broken)

* Isolated in `taylor.py`. Safe to ignore or replace later.

## Usage Examples

**Timeseries + heatmap:**

```python
uptime.plot_timeseries("sensor_uptime.csv", "CO2_30M_1")
uptime.plot_heatmap("sensor_uptime.csv", "CO2_30M_1")
```

**Scatter + difference:**

```python
validation.plot_scatter("lgr.csv", "scd41.csv", "LGR", "SCD41")
validation.plot_difference("lgr.csv", "scd41.csv", "LGR", "SCD41")
```

**QC summary:**

```python
qc.plot_qc_summary("sensor_10min.csv", "CO2_30M_1")
```

## Notes

* Works as drop-in replacement for the old file.
* All modules share consistent styling via `base.py`.
* Taylor diagram is not functional but does not affect other modules.