"""Visualization package for sensor data analysis

Modular visualization tools split by functionality:
- uptime: Uptime analysis plots
- validation: CO2 comparison and validation plots  
- quality_control: QC flag analysis
- taylor: Taylor diagrams (currently broken)

Example usage:
    from visualization import UptimePlots, ValidationPlots
    
    uptime = UptimePlots(output_dir="plots/")
    uptime.plot_timeseries("data/sensor_uptime.csv", "CO2_30M_1")
    
    validation = ValidationPlots(output_dir="plots/")
    validation.plot_scatter("data/lgr.csv", "data/scd41.csv", "LGR", "SCD41")

Or use the convenience function:
    from visualization import generate_all_plots
    generate_all_plots(config)
"""

from .base_plotter import BasePlotter
from .uptime_plots import UptimePlots
from .validation_plots import ValidationPlots
from .quality_control import QualityControlPlots
from .taylor_diagram_custom import TaylorDiagram, TaylorPlotter
TAYLOR_AVAILABLE = True

__all__ = [
    'BasePlotter',
    'UptimePlots',
    'ValidationPlots', 
    'QualityControlPlots',
    'TaylorDiagram',
    'generate_all_plots',
    'TAYLOR_AVAILABLE',
    'TaylorPlotter'
]


def generate_all_plots(config, show: bool = False, exclude: list = None):
    """
    Generate all standard plots using pipeline configuration.
    
    Routing:
    - Per-sensor plots   -> output/sensors/{name}/plots/
    - Multi-sensor plots -> output/merged/plots/
    
    Reads processed 10min CSVs and uptime CSVs from each sensor's
    csv/ directory via config.get_sensor_output_paths().
    
    Args:
        config: PipelineConfig object with sensor configuration
        show: If True, display plots inline in notebooks.
              If False (default), save only — figures are closed
              immediately to suppress notebook output.
        exclude: Optional list of plot categories to skip. Valid names:
              'uptime'          - per-sensor uptime timeseries + heatmap
              'qc'              - per-sensor QC flag summary
              'co2'             - per-sensor CO2 timeseries (full dataset)
              'monthly'         - per-sensor monthly CO2 timeseries
              'uptime_summary'  - multi-sensor uptime comparison
              'comparison'      - multi-sensor CO2 overlay
              'scatter'         - per-sensor scatter vs reference
              'difference'      - per-sensor difference vs reference
              'scatter_hue'     - 2x2 scatter panels coloured by temp/RH
              'timeseries_hue'  - stacked timeseries coloured by temp/RH
              'taylor'          - Taylor diagram
              'coverage_overlap'- Coverage Overlap Heatmap
    
    Example:
        generate_all_plots(config)                             # all plots, quiet
        generate_all_plots(config, show=True)                  # all + display
        generate_all_plots(config, exclude=['taylor', 'monthly'])  # skip these
    """
    import logging
    import re
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__)

    skip = set(exclude or [])
    close = not show   # close figures after save to suppress display

    merged_plots_dir = config.get_merged_dirs()['plots']

    # Shared plotters for multi-sensor / merged plots
    validation_plotter = ValidationPlots(merged_plots_dir, close_after_save=close)

    if TAYLOR_AVAILABLE and 'taylor' not in skip:
        taylor_plotter = TaylorPlotter(merged_plots_dir, close_after_save=close)
    else:
        if not TAYLOR_AVAILABLE and 'taylor' not in skip:
            logger.warning("Taylor diagrams skipped (SkillMetrics not installed). "
                           "Install with: pip install SkillMetrics")
        taylor_plotter = None

    logger.info("Generating plots...")

    uptime_csvs = {}       # sensor_name -> uptime CSV path
    data_csvs = {}         # sensor_name -> 10min CSV path
    sensor_names = [s.name for s in config.sensors]

    # -- 1. Per-sensor plots (-> sensors/{name}/plots/) -------------------
    for sensor_name in sensor_names:
        paths = config.get_sensor_output_paths(sensor_name)
        plots_dir = paths['plots_dir']
        uptime_csv = paths['uptime']
        data_csv = paths['csv']
        csv_dir = paths['csv_dir']

        # Per-sensor plotters save into the sensor's own plots/ dir
        uptime_plotter = UptimePlots(plots_dir, close_after_save=close)
        qc_plotter = QualityControlPlots(plots_dir, close_after_save=close)
        co2_plotter = ValidationPlots(plots_dir, close_after_save=close)

        if uptime_csv.exists():
            if 'uptime' not in skip:
                logger.info("  %s: Uptime timeseries", sensor_name)
                uptime_plotter.plot_timeseries(uptime_csv, sensor_name)

                logger.info("  %s: Uptime heatmap", sensor_name)
                uptime_plotter.plot_heatmap(uptime_csv, sensor_name)

            uptime_csvs[sensor_name] = uptime_csv
        else:
            logger.debug("  %s: No uptime CSV at %s", sensor_name, uptime_csv)

        if data_csv.exists():
            if 'qc' not in skip:
                logger.info("  %s: QC summary", sensor_name)
                qc_plotter.plot_qc_summary(data_csv, sensor_name)

            if 'co2' not in skip:
                # Per-sensor CO2 timeseries (full dataset)
                logger.info("  %s: CO2 timeseries (full)", sensor_name)
                co2_plotter.plot_co2_timeseries(data_csv, sensor_name)

            data_csvs[sensor_name] = data_csv
        else:
            logger.debug("  %s: No 10min CSV at %s", sensor_name, data_csv)

        # Monthly CO2 timeseries
        if 'monthly' not in skip:
            # Pattern: {sensor_name}_2024_09.csv (exclude _10min.csv, _uptime.csv)
            monthly_pattern = re.compile(
                rf'^{re.escape(sensor_name)}_\d{{4}}_\d{{2}}\.csv$'
            )
            monthly_csvs = sorted(
                f for f in csv_dir.iterdir()
                if f.is_file() and monthly_pattern.match(f.name)
            )
            for monthly_csv in monthly_csvs:
                # Extract period label like "2024_09"
                period = monthly_csv.stem.replace(f"{sensor_name}_", "")
                logger.info("  %s: CO2 timeseries (%s)", sensor_name, period)
                co2_plotter.plot_co2_timeseries(
                    monthly_csv, sensor_name, period_label=period)

    # -- 2. Multi-sensor summary plots (-> merged/plots/) -----------------
    uptime_summary_plotter = UptimePlots(merged_plots_dir, close_after_save=close)
    
    if len(uptime_csvs) > 1 and 'uptime_summary' not in skip:
        logger.info("  Multi-sensor uptime summary")
        uptime_summary_plotter.plot_summary(uptime_csvs)
    
    if 'coverage_overlap' not in skip:
        merged_uptime_csv = config.get_merged_dirs()['csv'] / "SMEAR_EE_CO2_uptime_merged.csv"
        if merged_uptime_csv.exists():
            logger.info("  Coverage overlap heatmap")
            uptime_summary_plotter.plot_coverage_overlap(merged_uptime_csv)

    if len(data_csvs) > 1 and 'comparison' not in skip:
        logger.info("  CO2 timeseries comparison")
        validation_plotter.plot_timeseries(data_csvs)

    # -- 3. Reference comparison (LGR) ------------------------------------
    ref_sensors = [s for s in config.sensors
                   if 'lgr' in s.sensor_type.lower()]
    if not ref_sensors:
        logger.warning("No LGR reference sensor found in config; "
                       "skipping validation plots")
        logger.info("Plot generation complete. Per-sensor: sensors/*/plots/, "
                    "multi-sensor: %s", merged_plots_dir)
        return

    ref_sensor = ref_sensors[0]
    ref_paths = config.get_sensor_output_paths(ref_sensor.name)
    lgr_csv = ref_paths['csv']

    if not lgr_csv.exists():
        logger.warning("LGR CSV not found at %s; "
                       "skipping reference comparison plots", lgr_csv)
        logger.info("Plot generation complete. Per-sensor: sensors/*/plots/, "
                    "multi-sensor: %s", merged_plots_dir)
        return

    test_sensors = [s.name for s in config.sensors
                    if s.name.startswith("CO2_")]

    for sensor_name in test_sensors:
        test_paths = config.get_sensor_output_paths(sensor_name)
        test_csv = test_paths['csv']

        if not test_csv.exists():
            logger.debug("  %s: No 10min CSV for validation", sensor_name)
            continue

        # Per-sensor validation plots -> that sensor's plots/ dir
        sensor_validation = ValidationPlots(
            test_paths['plots_dir'], close_after_save=close)

        if 'scatter' not in skip:
            logger.info("  %s vs %s: Scatter", sensor_name, ref_sensor.name)
            sensor_validation.plot_scatter(
                lgr_csv, test_csv, ref_sensor.name, sensor_name)

        if 'difference' not in skip:
            logger.info("  %s vs %s: Difference", sensor_name, ref_sensor.name)
            sensor_validation.plot_difference(
                lgr_csv, test_csv, ref_sensor.name, sensor_name)

    # -- 4. Hue-mapped panel plots (merged CSV -> merged/plots/) --------
    if 'scatter_hue' not in skip or 'timeseries_hue' not in skip:
        merged_csv_dir = config.get_merged_dirs()['csv']
        merged_csvs = sorted(merged_csv_dir.glob("*merged*.csv"))

        if not merged_csvs:
            logger.warning("No merged CSV found in %s; "
                           "skipping hue panel plots", merged_csv_dir)
        else:
            # Prefer the full merged file (no YYYY_MM date segment)
            # over monthly slices like *_2024_09_merged.csv
            monthly_pat = re.compile(r'_\d{4}_\d{2}_merged')
            full = [f for f in merged_csvs if not monthly_pat.search(f.stem)]
            merged_csv = full[0] if full else merged_csvs[-1]  # fallback: largest by name
            logger.info("  Loading merged CSV: %s", merged_csv.name)

            import pandas as _pd
            merged_df = _pd.read_csv(merged_csv)
            merged_df["timestamp"] = _pd.to_datetime(
                merged_df["timestamp"], format="mixed")

            try:
                lgr_co2_col, sensor_map = ValidationPlots.build_sensor_map(
                    merged_df, test_sensors)
            except ValueError as exc:
                logger.warning("Cannot build sensor map: %s", exc)
                sensor_map = []

            if sensor_map:
                hue_plotter = ValidationPlots(
                    merged_plots_dir, close_after_save=close)

                if 'scatter_hue' not in skip:
                    for hue in ("temp", "rh"):
                        cmap = "RdYlBu_r" if hue == "temp" else "cividis"
                        logger.info("  Scatter panel (%s hue)", hue)
                        hue_plotter.plot_scatter_panel_hue(
                            merged_df, lgr_co2_col, sensor_map,
                            hue_var=hue, cmap=cmap)

                if 'timeseries_hue' not in skip:
                    for hue in ("temp", "rh"):
                        cmap = "RdYlBu_r" if hue == "temp" else "cividis"
                        logger.info("  Timeseries (%s hue)", hue)
                        hue_plotter.plot_timeseries_hue(
                            merged_df, lgr_co2_col, sensor_map,
                            hue_var=hue, cmap=cmap)
            else:
                logger.warning("No SCD41 sensors found in merged CSV; "
                               "skipping hue panel plots")

    # Taylor diagram (multi-sensor -> merged/plots/)
    if 'taylor' not in skip:
        scd_csvs = {}
        for sensor_name in test_sensors:
            test_csv = config.get_sensor_output_paths(sensor_name)['csv']
            if test_csv.exists():
                scd_csvs[sensor_name] = test_csv

        if len(scd_csvs) > 0 and taylor_plotter is not None:
            logger.info("  Taylor diagram")
            taylor_fig = taylor_plotter.plot(lgr_csv, scd_csvs, ref_sensor.name)
            if close and taylor_fig is not None:
                plt.close(taylor_fig)
        elif taylor_plotter is None:
            logger.info("  Taylor diagram: Skipped (install SkillMetrics)")

    logger.info("Plot generation complete. Per-sensor: sensors/*/plots/, "
                "multi-sensor: %s", merged_plots_dir)