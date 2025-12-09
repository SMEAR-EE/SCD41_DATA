"""Taylor diagram visualization using SkillMetrics package

Uses the SkillMetrics package for publication-quality Taylor diagrams.
Reference: Taylor, K. E. (2001), Summarizing multiple aspects of model
performance in a single diagram, J. Geophys. Res., 106(D7), 7183-7192.

Installation:
    pip install SkillMetrics

GitHub: https://github.com/PeterRochford/SkillMetrics
"""

from pathlib import Path
from typing import Dict, Optional
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
    """Generate Taylor diagrams using SkillMetrics package
    
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
    
    def plot(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "Reference",
        title: str = "Taylor Diagram: Multi-Sensor Comparison",
        marker_colors: Optional[list] = None,
        marker_symbols: Optional[list] = None,
        save: bool = True
    ) -> plt.Figure:
        """
        Create Taylor diagram comparing multiple sensors to reference
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path}
            reference_name: Name of reference sensor (for plot label)
            title: Plot title
            marker_colors: List of colors for each sensor (default: auto)
            marker_symbols: List of marker symbols for each sensor (default: auto)
            save: If True, save to output_dir
            
        Returns:
            Matplotlib figure with Taylor diagram
        """
        # Load reference data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = 'co2_mean' if 'co2_mean' in ref.columns else 'co2'
        
        # Calculate statistics for each test sensor
        stats_list = []
        labels = []
        
        for test_name, test_csv in test_csvs.items():
            test = pd.read_csv(test_csv, parse_dates=['timestamp'])
            test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
            
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
                f"σ={stats['sdev'][1]:.2f}, "
                f"CRMSD={stats['crmsd'][1]:.2f}"
            )
        
        if not stats_list:
            self.logger.error("No valid sensor data to plot")
            return None
        
        # Prepare data for plotting
        sdev = np.array([s['sdev'][1] for s in stats_list])
        crmsd = np.array([s['crmsd'][1] for s in stats_list])
        ccoef = np.array([s['ccoef'][1] for s in stats_list])
        
        # Default colors and markers if not provided
        if marker_colors is None:
            # Use colorblind-friendly palette
            marker_colors = ['b', 'r', 'g', 'm', 'c', 'y', 'k']
            marker_colors = marker_colors[:len(stats_list)]
        
        if marker_symbols is None:
            marker_symbols = ['o', 's', '^', 'd', 'v', '<', '>']
            marker_symbols = marker_symbols[:len(stats_list)]
        
        # Create Taylor diagram
        fig = plt.figure(figsize=(10, 10))
        
        sm.taylor_diagram(
            sdev, crmsd, ccoef,
            markerLabel=labels,
            markerColor=marker_colors,
            markerSymbol=marker_symbols,
            markerSize=10,
            titleRMS='off',  # Turn off default RMS title
            tickRMS=[0.5, 1.0, 1.5, 2.0],  # RMS contours
            tickSTD=[0.5, 1.0, 1.5, 2.0],  # STD tick marks
            colRMS='gray',
            styleRMS='--',
            widthRMS=1.0,
            titleSTD='Normalized Standard Deviation',
            titleCOR='Correlation Coefficient',
            alpha=0.8,
            axismax=2.0  # Maximum axis value
        )
        
        # Add custom title
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Adjust layout
        plt.tight_layout()
        
        if save:
            filename = "taylor_diagram_skillmetrics.png"
            self._save_figure(plt.gcf(), filename)
        
        return fig
    
    def plot_normalized(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "Reference",
        title: str = "Normalized Taylor Diagram",
        save: bool = True
    ) -> plt.Figure:
        """
        Create normalized Taylor diagram
        
        In normalized diagrams, all standard deviations are divided by
        the reference standard deviation, making the reference point at (1, 0).
        This is useful for comparing sensors with different absolute magnitudes.
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path}
            reference_name: Name of reference sensor
            title: Plot title
            save: If True, save to output_dir
            
        Returns:
            Matplotlib figure with normalized Taylor diagram
        """
        # Load reference data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = 'co2_mean' if 'co2_mean' in ref.columns else 'co2'
        
        # Calculate statistics for each test sensor
        stats_list = []
        labels = []
        
        for test_name, test_csv in test_csvs.items():
            test = pd.read_csv(test_csv, parse_dates=['timestamp'])
            test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
            
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
            
            # Calculate normalized Taylor statistics
            stats = sm.taylor_statistics(
                merged[test_col].values,
                merged[ref_col].values,
                field='norm'  # Normalized statistics
            )
            
            stats_list.append(stats)
            labels.append(test_name)
        
        if not stats_list:
            self.logger.error("No valid sensor data to plot")
            return None
        
        # Prepare data for plotting
        sdev = np.array([s['sdev'][1] for s in stats_list])
        crmsd = np.array([s['crmsd'][1] for s in stats_list])
        ccoef = np.array([s['ccoef'][1] for s in stats_list])
        
        # Create normalized Taylor diagram
        fig = plt.figure(figsize=(10, 10))
        
        sm.taylor_diagram(
            sdev, crmsd, ccoef,
            markerLabel=labels,
            markerColor='r',
            markerSize=10,
            tickRMS=[0.5, 1.0, 1.5, 2.0],
            tickSTD=[0.5, 1.0, 1.5, 2.0],
            colRMS='gray',
            styleRMS='--',
            titleSTD='Normalized Standard Deviation',
            titleCOR='Correlation Coefficient',
            alpha=0.8
        )
        
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        
        if save:
            filename = "taylor_diagram_normalized.png"
            self._save_figure(plt.gcf(), filename)
        
        return fig