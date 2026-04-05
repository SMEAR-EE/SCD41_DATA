# Visualization Module

Modular plotting package for sensor data visualization with uptime, validation, and QC plots.

## Quick Start

```python
from src.visualization import generate_all_plots
generate_all_plots(config)  # Generate all plots at once
```

Or use individual plotters:

```python
from src.visualization import UptimePlots, ValidationPlots, QualityControlPlots

uptime = UptimePlots("plots/")
validation = ValidationPlots("plots/")
qc = QualityControlPlots("plots/")
```

## Available Plotters

### UptimePlots
- `plot_timeseries(csv, sensor)` - Time series with data availability
- `plot_heatmap(csv, sensor)` - Calendar heatmap showing gaps
- `plot_summary(csv_dict)` - Multi-sensor comparison
- `plot_coverage_overlap(merged_csv)` - Multi-sensor coverage overlap heatmap with LGR absence

### ValidationPlots
- `plot_timeseries(data_csvs, start_date, end_date)` - Overlay multiple sensors
- `plot_scatter(reference_csv, test_csv, ref_name, test_name)` - Sensor vs reference
- `plot_difference(reference_csv, test_csv, ref_name, test_name)` - Bias analysis
- `plot_co2_timeseries(data, sensor_name, period_label)` - Single-sensor CO2 timeseries with summary statistics
- `plot_scatter_panel_hue(merged, lgr_co2_col, sensors, hue_var, cmap)` - 2×2 scatter grid coloured by temperature or relative humidity
- `plot_timeseries_hue(merged, lgr_co2_col, sensors, hue_var, cmap)` - Stacked timeseries panels coloured by temperature or relative humidity
- `build_sensor_map(merged_df, sensor_names)` - Auto-discover column mappings from merged CSV
- `plot_timeseries_seasonal(merged, lgr_co2_col, sensors, hue_var, cmap)` - Seasonal-shaded timeseries with winter/summer bands and temperature hue
- `plot_monthly_bias_boxplot(merged, lgr_co2_col, sensors, seasonal_shading, show_fliers)` - Monthly boxplot of SCD41−LGR residuals (30 m sensors)

### QualityControlPlots
- `plot_qc_summary(data_csv, sensor_name)` - QC flag distribution

### TaylorDiagram
- `__init__(STD, fig, rect, label, smax, extend_negative)` - Initialise the polar floating-axes diagram
- `from_stats(ref_std, correlations, fig, rect, label, smax)` - Factory method: auto-detect negative correlations
- `add_sample(STD, r)` - Plot a single sample point on the diagram
- `add_contours(levels)` - Overlay RMSE contour lines
- `queue_offchart(STD, r, label, marker, color, markersize)` - Register an off-chart point for later batch drawing
- `flush_offchart(base_fraction, arrow_zone, min_arrow)` - Draw all queued off-chart points with proportional arrows
- `add_offchart_arrow(STD, r, label, marker, color, markersize, offset_fraction)` - Draw a single off-chart arrow immediately (legacy)

### TaylorPlotter
- `plot(ref_csv, scd_csvs, ref_name, title, filename)` - Build a Taylor diagram comparing SCD41 sensors against a reference

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