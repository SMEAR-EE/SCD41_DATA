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
# from .taylor_diagram_custom import TaylorPlotter
# Taylor diagram requires optional SkillMetrics package
try:
    from .taylor_plots import TaylorDiagram
    TAYLOR_AVAILABLE = True
except ImportError:
    TAYLOR_AVAILABLE = False
    TaylorDiagram = None

__all__ = [
    'BasePlotter',
    'UptimePlots',
    'ValidationPlots', 
    'QualityControlPlots',
    'TaylorDiagram',
    'generate_all_plots',
    'TAYLOR_AVAILABLE'
]


def generate_all_plots(config, show: bool = False):
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
    
    Example:
        generate_all_plots(config)              # save only, quiet
        generate_all_plots(config, show=True)   # save + display inline
    """
    import logging
    import re
    import matplotlib.pyplot as plt
    logger = logging.getLogger(__name__)

    close = not show   # close figures after save to suppress display

    merged_plots_dir = config.get_merged_dirs()['plots']

    # Shared plotters for multi-sensor / merged plots
    validation_plotter = ValidationPlots(merged_plots_dir, close_after_save=close)

    if TAYLOR_AVAILABLE:
        taylor_plotter = TaylorDiagram(merged_plots_dir)
    else:
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
            logger.info("  %s: Uptime timeseries", sensor_name)
            uptime_plotter.plot_timeseries(uptime_csv, sensor_name)

            logger.info("  %s: Uptime heatmap", sensor_name)
            uptime_plotter.plot_heatmap(uptime_csv, sensor_name)

            uptime_csvs[sensor_name] = uptime_csv
        else:
            logger.debug("  %s: No uptime CSV at %s", sensor_name, uptime_csv)

        if data_csv.exists():
            logger.info("  %s: QC summary", sensor_name)
            qc_plotter.plot_qc_summary(data_csv, sensor_name)

            # Per-sensor CO2 timeseries (full dataset)
            logger.info("  %s: CO2 timeseries (full)", sensor_name)
            co2_plotter.plot_co2_timeseries(data_csv, sensor_name)

            data_csvs[sensor_name] = data_csv
        else:
            logger.debug("  %s: No 10min CSV at %s", sensor_name, data_csv)

        # Monthly CO2 timeseries
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
    if len(uptime_csvs) > 1:
        logger.info("  Multi-sensor uptime summary")
        uptime_summary_plotter = UptimePlots(
            merged_plots_dir, close_after_save=close)
        uptime_summary_plotter.plot_summary(uptime_csvs)

    if len(data_csvs) > 1:
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

        logger.info("  %s vs %s: Scatter", sensor_name, ref_sensor.name)
        sensor_validation.plot_scatter(
            lgr_csv, test_csv, ref_sensor.name, sensor_name)

        logger.info("  %s vs %s: Difference", sensor_name, ref_sensor.name)
        sensor_validation.plot_difference(
            lgr_csv, test_csv, ref_sensor.name, sensor_name)

    # Taylor diagram (multi-sensor -> merged/plots/)
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