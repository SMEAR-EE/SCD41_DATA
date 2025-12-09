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


def generate_all_plots(config):
    """
    Generate all standard plots using pipeline configuration.
    
    Automatically reads:
    - config.output_dir  → processed 10min CSVs + uptime CSVs
    - config.plots_dir   → where to save plots
    
    Args:
        config: PipelineConfig object with sensor configuration
    """
    from pathlib import Path
    
    individual_dir = config.output_dir
    output_dir = config.plots_dir
    sensor_names = [s.name for s in config.sensors]
    
    # Initialize plotters
    uptime_plotter = UptimePlots(output_dir)
    validation_plotter = ValidationPlots(output_dir)
    qc_plotter = QualityControlPlots(output_dir)
    
    # Taylor diagram only if SkillMetrics is installed
    if TAYLOR_AVAILABLE:
        taylor_plotter = TaylorDiagram(output_dir)
    else:
        print("  ⚠ Taylor diagrams skipped (SkillMetrics not installed)")
        print("    Install with: pip install SkillMetrics")
        taylor_plotter = None
    
    print("Generating plots...")
    
    uptime_csvs = {}
    data_csvs = {}
    
    # 1. Per-sensor plots
    for sensor in sensor_names:
        uptime_csv = individual_dir / f"{sensor}_uptime.csv"
        data_csv = individual_dir / f"{sensor}_10min.csv"
        
        if uptime_csv.exists():
            print(f"  - {sensor}: Uptime timeseries")
            uptime_plotter.plot_timeseries(uptime_csv, sensor)
            
            print(f"  - {sensor}: Uptime heatmap")
            uptime_plotter.plot_heatmap(uptime_csv, sensor)
            
            uptime_csvs[sensor] = uptime_csv
        
        if data_csv.exists():
            print(f"  - {sensor}: QC summary")
            qc_plotter.plot_qc_summary(data_csv, sensor)
            data_csvs[sensor] = data_csv
    
    # 2. Multi-sensor summary plots
    if len(uptime_csvs) > 1:
        print("  - Multi-sensor uptime summary")
        uptime_plotter.plot_summary(uptime_csvs)
    
    if len(data_csvs) > 1:
        print("  - CO2 timeseries comparison")
        validation_plotter.plot_timeseries(data_csvs)
    
    # 3. Reference comparison (LGR)
    lgr_csv = individual_dir / "LGR_30M_10min.csv"
    if lgr_csv.exists():
        test_sensors = [s for s in sensor_names if s.startswith("CO2_")]
        
        for sensor in test_sensors:
            test_csv = individual_dir / f"{sensor}_10min.csv"
            if test_csv.exists():
                print(f"  - {sensor} vs LGR: Scatter")
                validation_plotter.plot_scatter(lgr_csv, test_csv, "LGR", sensor)
                
                print(f"  - {sensor} vs LGR: Difference")
                validation_plotter.plot_difference(lgr_csv, test_csv, "LGR", sensor)
        
        scd_csvs = {s: individual_dir / f"{s}_10min.csv"
                    for s in test_sensors
                    if (individual_dir / f"{s}_10min.csv").exists()}
        
        if len(scd_csvs) > 1:
            if taylor_plotter is not None:
                print("  - Taylor diagram")
                taylor_plotter.plot(lgr_csv, scd_csvs, "LGR")
            else:
                print("  - Taylor diagram: Skipped (install SkillMetrics)")
    
    print(f"\n✓ All plots saved to: {output_dir}")