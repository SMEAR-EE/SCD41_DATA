"""Professional Taylor diagram visualization for CO2 sensor validation

Uses the SkillMetrics package with enhanced styling and config integration.
Reference: Taylor, K. E. (2001), Summarizing multiple aspects of model
performance in a single diagram, J. Geophys. Res., 106(D7), 7183-7192.

Installation:
    pip install SkillMetrics

GitHub: https://github.com/PeterRochford/SkillMetrics
"""

from pathlib import Path
from typing import Dict, Optional, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .base_plotter import BasePlotter

# Try to import skill_metrics
try:
    import skill_metrics as sm
    SKILL_METRICS_AVAILABLE = True
except ImportError:
    SKILL_METRICS_AVAILABLE = False


class TaylorDiagram(BasePlotter):
    """Generate publication-quality Taylor diagrams using SkillMetrics
    
    Taylor diagrams show three statistics simultaneously:
    - Correlation coefficient (angular position)
    - Standard deviation (radial distance)  
    - Centered RMSD (distance from reference point)
    
    Requires: pip install SkillMetrics
    """
    
    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: Where to save plots
            
        Raises:
            ImportError: If SkillMetrics package not installed
        """
        super().__init__(output_dir)
        
        if not SKILL_METRICS_AVAILABLE:
            raise ImportError(
                "SkillMetrics package not found. Install with:\n"
                "  pip install SkillMetrics\n"
                "Or visit: https://github.com/PeterRochford/SkillMetrics"
            )
    
    def _detect_co2_column(self, df: pd.DataFrame, sensor_name: str) -> str:
        """Detect the CO2 column name in the dataframe
        
        Args:
            df: DataFrame to search
            sensor_name: Name of sensor (for error messages)
            
        Returns:
            Column name containing CO2 data
            
        Raises:
            ValueError: If no CO2 column found
        """
        # Try common CO2 column names (order matters - most specific first)
        # Covers both aggregated data (_mean suffix) and raw data
        possible_cols = [
            'CO2_dry_mean',  # LGR aggregated data
            'co2_dry_mean',  # Lowercase variant
            'CO2_dry',       # LGR raw data
            'co2_dry',       # Lowercase variant
            'co2_mean',      # SCD41 aggregated data
            'co2',           # SCD41 raw data
            'CO2'            # Uppercase variant
        ]
        
        for col in possible_cols:
            if col in df.columns:
                self.logger.debug(f"{sensor_name}: Using column '{col}' for CO2 data")
                return col
        
        # No match found
        raise ValueError(
            f"No CO2 column found for {sensor_name}. "
            f"Available columns: {list(df.columns)}"
        )
    
    def plot_from_config(
        self,
        config,
        test_sensor_ids: Optional[List[str]] = None,
        title: str = "Taylor Diagram: Multi-Sensor CO₂ Comparison",
        normalize: bool = True,
        save: bool = True
    ) -> plt.Figure:
        """
        Create Taylor diagram using paths from config
        
        Args:
            config: PipelineConfig object or dict with sensor configuration
            test_sensor_ids: List of test sensor IDs (e.g., ['CO2_30M_A', 'CO2_30M_B'])
                           If None, uses all test sensors from config
            title: Plot title
            normalize: If True, normalize by reference std dev (recommended)
            save: If True, save to output_dir
            
        Returns:
            Matplotlib figure with Taylor diagram
        """
        # Handle both PipelineConfig objects and dicts
        if hasattr(config, 'output_dir'):
            # It's a PipelineConfig object
            # config.output_dir already points to 'output/individual'
            output_dir = Path(config.output_dir)
            
            # Get reference sensor (sensor_type contains 'lgr' or is 'reference')
            ref_sensor = None
            for s in config.sensors:
                sensor_type_lower = s.sensor_type.lower()
                if 'lgr' in sensor_type_lower or sensor_type_lower == 'reference':
                    ref_sensor = s
                    break
            
            if ref_sensor is None:
                raise ValueError(
                    f"No reference sensor found in config. "
                    f"Available sensor types: {[s.sensor_type for s in config.sensors]}"
                )
            
            ref_csv = output_dir / f"{ref_sensor.name}_10min.csv"
            ref_name = ref_sensor.name
            
            # Get test sensors (all non-LGR sensors)
            test_sensors = [s for s in config.sensors if 'lgr' not in s.sensor_type.lower()]
            
            if test_sensor_ids is not None:
                # Filter to only requested sensors
                test_sensors = [s for s in test_sensors if s.name in test_sensor_ids or (s.sensor_id and s.sensor_id in test_sensor_ids)]
            
            # Build test sensor dict
            test_csvs = {}
            for sensor in test_sensors:
                test_csvs[sensor.name] = output_dir / f"{sensor.name}_10min.csv"
        
        else:
            # It's a dict - legacy support
            output_dir = Path(config['output']['directories']['individual'])
            
            # Get reference sensor path
            ref_csv = output_dir / f"{config['sensors']['reference']['id']}_10min.csv"
            ref_name = config['sensors']['reference']['name']
            
            # Build test sensor dict
            if test_sensor_ids is None:
                test_sensor_ids = [s['id'] for s in config['sensors']['test']]
            
            test_csvs = {}
            for sensor_id in test_sensor_ids:
                sensor_cfg = next((s for s in config['sensors']['test'] if s['id'] == sensor_id), None)
                if sensor_cfg:
                    test_csvs[sensor_cfg['name']] = output_dir / f"{sensor_id}_10min.csv"
                else:
                    test_csvs[sensor_id] = output_dir / f"{sensor_id}_10min.csv"
        
        self.logger.info(f"Plotting from config: {ref_name} vs {list(test_csvs.keys())}")
        
        if normalize:
            return self.plot_normalized(ref_csv, test_csvs, ref_name, title, save)
        else:
            return self.plot(ref_csv, test_csvs, ref_name, title, save=save)
    
    def plot(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "Reference",
        title: str = "Taylor Diagram: Multi-Sensor CO₂ Comparison",
        marker_colors: Optional[list] = None,
        marker_symbols: Optional[list] = None,
        save: bool = True,
        filename: str = "taylor_diagram.png"
    ) -> plt.Figure:
        """
        Create Taylor diagram comparing multiple sensors to reference
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path}
            reference_name: Name of reference sensor (for plot label)
            title: Plot title
            marker_colors: List of colors for each sensor
            marker_symbols: List of marker symbols for each sensor
            save: If True, save to output_dir
            filename: Output filename
            
        Returns:
            Matplotlib figure with Taylor diagram
        """
        self.logger.info(f"Creating Taylor diagram with {len(test_csvs)} test sensors")
        
        # Load reference data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = self._detect_co2_column(ref, reference_name)
        self.logger.info(f"Reference sensor: {reference_name}, column: {ref_col}, points: {len(ref)}")
        
        # Calculate statistics for each test sensor
        stats_list = []
        labels = []
        
        for test_name, test_csv in test_csvs.items():
            self.logger.debug(f"Processing test sensor: {test_name}")
            
            test = pd.read_csv(test_csv, parse_dates=['timestamp'])
            test_col = self._detect_co2_column(test, test_name)
            
            # Merge on timestamp
            merged = pd.merge(
                ref[['timestamp', ref_col]],
                test[['timestamp', test_col]],
                on='timestamp',
                how='inner'
            ).dropna()
            
            if len(merged) == 0:
                self.logger.warning(f"No overlapping data for {test_name}, skipping")
                continue
            
            self.logger.info(f"{test_name}: {len(merged)} overlapping data points")
            
            # Calculate Taylor statistics using SkillMetrics
            stats = sm.taylor_statistics(
                merged[test_col].values,
                merged[ref_col].values
            )
            
            stats_list.append(stats)
            labels.append(test_name)
            
            # Log statistics
            self.logger.info(
                f"{test_name}: "
                f"r={stats['ccoef'][1]:.3f}, "
                f"σ={stats['sdev'][1]:.2f} ppm, "
                f"CRMSD={stats['crmsd'][1]:.2f} ppm"
            )
        
        if not stats_list:
            self.logger.error("No valid sensor data to plot")
            return None
        
        # Prepare data for plotting
        sdev = np.array([s['sdev'][1] for s in stats_list])
        crmsd = np.array([s['crmsd'][1] for s in stats_list])
        ccoef = np.array([s['ccoef'][1] for s in stats_list])
        
        # Default colors: publication-quality colorblind-friendly palette
        if marker_colors is None:
            # Colors from ColorBrewer Set2 (colorblind-safe)
            marker_colors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02']
        
        if marker_symbols is None:
            marker_symbols = ['o', 's', '^', 'd', 'v', 'p']
        
        # Ensure we have enough colors/symbols
        marker_colors = (marker_colors * ((len(stats_list) // len(marker_colors)) + 1))[:len(stats_list)]
        marker_symbols = (marker_symbols * ((len(stats_list) // len(marker_symbols)) + 1))[:len(stats_list)]
        
        self.logger.info("Generating Taylor diagram plot")
        
        # Create figure with better size for publication
        fig = plt.figure(figsize=(8, 8))
        
        # Calculate appropriate axis limits
        max_std = max(sdev)
        ref_std = stats_list[0]['sdev'][0]  # Reference std dev
        max_rmsd = max(crmsd)
        axis_max = max(max_std, max_rmsd, ref_std) * 1.15
        
        # Calculate appropriate tick marks (5 levels)
        tick_interval = axis_max / 5
        tick_marks = [round(tick_interval * i, 1) for i in range(1, 6)]
        
        self.logger.info(f"Taylor diagram: axis_max={axis_max:.1f}, ref_std={ref_std:.1f}")
        
        # Plot each sensor individually for better control
        for i, (label, color, symbol) in enumerate(zip(labels, marker_colors, marker_symbols)):
            sm.taylor_diagram(
                np.array([sdev[i]]),
                np.array([crmsd[i]]),
                np.array([ccoef[i]]),
                markerLabel=[label],
                markerLabelColor='black',
                markerLegend='on',
                markerColor=color,
                markerSymbol=symbol,
                markerSize=12,
                styleOBS='-',  # Solid line for observed
                colOBS='black',
                markerOBS='o',
                titleOBS='',
                overlay='on' if i > 0 else 'off',  # Overlay after first
                tickRMS=tick_marks,
                tickSTD=tick_marks,
                tickRMSangle=110,
                colRMS='gray',
                styleRMS=':',
                widthRMS=1.5,
                titleRMS='off',
                titleSTD='on',
                titleCOR='on',
                colCOR='black',
                colSTD='black',
                styleSTD='--',
                widthSTD=1.0,
                axismax=axis_max,
                alpha=0.0  # No fill
            )
        
        # Enhance the plot
        ax = plt.gca()
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        
        # Improve legend
        legend = ax.legend(loc='upper right', frameon=True, fontsize=10)
        legend.get_frame().set_alpha(0.95)
        legend.get_frame().set_edgecolor('gray')
        
        plt.tight_layout()
        
        if save:
            self._save_figure(fig, filename)
            self.logger.info(f"Saved Taylor diagram to {self.output_dir / filename}")
        
        return fig
    
    def plot_normalized(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "Reference",
        title: str = "Normalized Taylor Diagram: Multi-Sensor CO₂ Comparison",
        save: bool = True,
        filename: str = "taylor_diagram_normalized.png"
    ) -> plt.Figure:
        """
        Create normalized Taylor diagram (RECOMMENDED for sensor comparison)
        
        In normalized diagrams, all standard deviations are divided by
        the reference standard deviation, making the reference point at (1, 0).
        This is the standard approach for model evaluation and sensor comparison.
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path}
            reference_name: Name of reference sensor
            title: Plot title
            save: If True, save to output_dir
            filename: Output filename
            
        Returns:
            Matplotlib figure with normalized Taylor diagram
        """
        self.logger.info(f"Creating NORMALIZED Taylor diagram with {len(test_csvs)} test sensors")
        
        # Load reference data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = self._detect_co2_column(ref, reference_name)
        self.logger.info(f"Reference sensor: {reference_name}, column: {ref_col}")
        
        # Calculate statistics for each test sensor
        stats_list = []
        labels = []
        
        # Colors from ColorBrewer Dark2 (publication quality)
        colors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02', '#a6761d']
        symbols = ['o', 's', '^', 'd', 'v', 'p', 'h']
        
        for test_name, test_csv in test_csvs.items():
            self.logger.debug(f"Processing test sensor: {test_name}")
            
            test = pd.read_csv(test_csv, parse_dates=['timestamp'])
            test_col = self._detect_co2_column(test, test_name)
            
            # Merge on timestamp
            merged = pd.merge(
                ref[['timestamp', ref_col]],
                test[['timestamp', test_col]],
                on='timestamp',
                how='inner'
            ).dropna()
            
            if len(merged) == 0:
                self.logger.warning(f"No overlapping data for {test_name}, skipping")
                continue
            
            self.logger.info(f"{test_name}: {len(merged)} overlapping data points")
            
            # Calculate NORMALIZED Taylor statistics
            stats = sm.taylor_statistics(
                merged[test_col].values,
                merged[ref_col].values,
                field='norm'  # KEY: Normalized statistics
            )
            
            stats_list.append(stats)
            labels.append(test_name)
            
            # Log normalized statistics
            self.logger.info(
                f"{test_name} (normalized): "
                f"r={stats['ccoef'][1]:.3f}, "
                f"σ/σ_ref={stats['sdev'][1]:.3f}, "
                f"CRMSD'={stats['crmsd'][1]:.3f}"
            )
        
        if not stats_list:
            self.logger.error("No valid sensor data to plot")
            return None
        
        # Prepare normalized data
        sdev = np.array([s['sdev'][1] for s in stats_list])
        crmsd = np.array([s['crmsd'][1] for s in stats_list])
        ccoef = np.array([s['ccoef'][1] for s in stats_list])
        
        # For normalized diagram, calculate appropriate axis max
        # Don't cap it if the data exceeds typical ranges
        max_val = max(np.max(sdev), np.max(crmsd), 1.0) * 1.15
        
        # Only use standard 2.0 cap if data is within reasonable range
        if max_val <= 2.5:
            axis_max = 2.0
            tick_marks = [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]
        else:
            # Large deviations - use auto-scaling
            axis_max = max_val
            # Calculate reasonable tick marks
            n_ticks = 8
            tick_interval = axis_max / n_ticks
            tick_marks = [round(tick_interval * i, 1) for i in range(1, n_ticks + 1)]
        
        tick_marks = [t for t in tick_marks if t <= axis_max]
        
        self.logger.info(f"Normalized diagram: axis_max={axis_max:.2f}, max_sdev={np.max(sdev):.2f}")
        
        # Warn if sensors show very poor performance
        if np.max(sdev) > 10:
            self.logger.warning(
                f"Large normalized standard deviations detected (max={np.max(sdev):.1f}). "
                f"This indicates test sensors have much higher variability than the reference sensor, "
                f"suggesting poor correlation and/or systematic differences."
            )
        
        # Create figure
        fig = plt.figure(figsize=(8, 8))
        
        # Plot each sensor with distinct markers
        for i, label in enumerate(labels):
            color = colors[i % len(colors)]
            symbol = symbols[i % len(symbols)]
            
            sm.taylor_diagram(
                np.array([sdev[i]]),
                np.array([crmsd[i]]),
                np.array([ccoef[i]]),
                markerLabel=[label],
                markerLabelColor='black',
                markerLegend='on',
                markerColor=color,
                markerSymbol=symbol,
                markerSize=12,
                styleOBS='-',
                colOBS='black',
                markerOBS='o',
                titleOBS='',
                overlay='on' if i > 0 else 'off',
                tickRMS=tick_marks,
                tickSTD=tick_marks,
                tickRMSangle=110,
                colRMS='gray',
                styleRMS=':',
                widthRMS=1.5,
                titleRMS='off',
                titleSTD='on',
                titleCOR='on',
                colCOR='black',
                colSTD='black',
                styleSTD='--',
                widthSTD=1.0,
                axismax=axis_max,
                alpha=0.0
            )
        
        # Enhance plot
        ax = plt.gca()
        # Use plain text CO2 instead of subscript to avoid font issues
        title_clean = title.replace('CO₂', 'CO2')
        ax.set_title(title_clean, fontsize=14, fontweight='bold', pad=15)
        
        # Add subtitle explaining normalization (plain text)
        ax.text(
            0.5, -0.08,
            'Standard deviations normalized by reference sensor',
            ha='center', va='top', transform=ax.transAxes,
            fontsize=9, style='italic', color='gray'
        )
        
        # Improve legend
        try:
            legend = ax.legend(loc='upper right', frameon=True, fontsize=10)
            legend.get_frame().set_alpha(0.95)
            legend.get_frame().set_edgecolor('gray')
        except UserWarning:
            # No legend items, that's okay
            pass
        
        plt.tight_layout()
        
        if save:
            self._save_figure(fig, filename)
            self.logger.info(f"Saved normalized Taylor diagram to {self.output_dir / filename}")
        
        return fig