"""CO2 validation visualization tools

Compare test sensors against reference measurements.
Includes timeseries, scatter plots, and difference analyses.
"""

from pathlib import Path
from typing import Dict, Optional
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from .base_plotter import BasePlotter


class ValidationPlots(BasePlotter):
    """Generate validation plots comparing sensors"""
    
    def plot_timeseries(
        self,
        data_csvs: Dict[str, Path],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot CO2 timeseries for multiple sensors.
        
        Overlays CO2 measurements from multiple sensors on a single plot for
        visual comparison of temporal patterns. Useful for identifying sensor
        drift, calibration issues, or measurement inconsistencies.
        
        Args:
            data_csvs: Dict mapping sensor names to 10min CSV paths
                       Example: {'LGR_30M': Path('LGR_30M_10min.csv'), ...}
            start_date: Optional start date filter in 'YYYY-MM-DD' format
            end_date: Optional end date filter in 'YYYY-MM-DD' format
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the timeseries plot
        """
        fig, ax = plt.subplots(figsize=(16, 6))
        
        for sensor_name, csv_path in data_csvs.items():
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            
            # Filter date range
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # Get CO2 column
            co2_col = self._detect_co2_column(df)
            
            # Plot
            ax.plot(df['timestamp'], df[co2_col], label=sensor_name,
                    alpha=0.7, marker='.', markersize=1.5, linewidth=0.8)
        
        ax.set_ylabel('CO₂ (ppm)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title('CO₂ Timeseries Comparison', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            filename = "co2_timeseries_comparison.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_scatter(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str,
        test_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Scatter plot: reference vs test sensor.
        
        Creates a scatter plot comparing test sensor measurements against
        reference sensor measurements. Includes 1:1 line and validation
        statistics (correlation, RMSE, bias, sample count).
        
        Args:
            reference_csv: Path to reference sensor 10min CSV (e.g., LGR)
            test_csv: Path to test sensor 10min CSV (e.g., SCD41)
            reference_name: Reference sensor name for axis labels
            test_name: Test sensor name for axis labels
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the scatter plot, or None if
            no overlapping data exists between sensors
        """
        # Load data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        # Get CO2 columns
        ref_col = self._detect_co2_column(ref)
        test_col = self._detect_co2_column(test)
        
        # Merge on timestamp
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        ).dropna()
        
        if len(merged) == 0:
            self.logger.warning(f"No overlapping data between {reference_name} and {test_name}")
            return None
        
        # Calculate stats
        corr = np.corrcoef(merged[ref_col], merged[test_col])[0, 1]
        rmse = np.sqrt(np.mean((merged[ref_col] - merged[test_col])**2))
        bias = np.mean(merged[test_col] - merged[ref_col])
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Scatter
        ax.scatter(merged[ref_col], merged[test_col], 
                  alpha=0.5, s=10, color='steelblue')
        
        # 1:1 line
        min_val = min(merged[ref_col].min(), merged[test_col].min())
        max_val = max(merged[ref_col].max(), merged[test_col].max())
        ax.plot([min_val, max_val], [min_val, max_val], 
               'r--', linewidth=2, label='1:1 Line')
        
        # Stats text
        stats_text = f'R = {corr:.3f}\nRMSE = {rmse:.2f} ppm\nBias = {bias:.2f} ppm\nn = {len(merged)}'
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Styling
        ax.set_xlabel(f'{reference_name} CO₂ (ppm)', fontsize=12)
        ax.set_ylabel(f'{test_name} CO₂ (ppm)', fontsize=12)
        ax.set_title(f'Scatter: {test_name} vs {reference_name}',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        
        if save:
            filename = f"scatter_{test_name}_vs_{reference_name}.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_difference(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str,
        test_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot difference (test - reference) over time.
        
        Creates a two-panel plot for bias analysis:
        - Top panel: Difference timeseries with zero line and mean bias
        - Bottom panel: Histogram of differences showing distribution
        
        Useful for identifying systematic bias, drift over time, and
        outliers in sensor measurements.
        
        Args:
            reference_csv: Path to reference sensor 10min CSV
            test_csv: Path to test sensor 10min CSV
            reference_name: Reference sensor name for labels
            test_name: Test sensor name for labels
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object with two subplots, or None if no
            overlapping data exists between sensors
        """
        # Load data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        # Get CO2 columns
        ref_col = self._detect_co2_column(ref)
        test_col = self._detect_co2_column(test)
        
        # Merge on timestamp
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        ).dropna()
        
        if len(merged) == 0:
            self.logger.warning(f"No overlapping data between {reference_name} and {test_name}")
            return None
        
        # Calculate difference
        merged['diff'] = merged[test_col] - merged[ref_col]
        
        # Stats
        mean_diff = merged['diff'].mean()
        std_diff = merged['diff'].std()
        
        # Create 2-panel plot
        fig = plt.figure(figsize=(16, 8))
        gs = GridSpec(2, 1, height_ratios=[2, 1])
        
        # Panel 1: Timeseries
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(merged['timestamp'], merged['diff'], 
                color='steelblue', alpha=0.7, linewidth=0.8,
                marker='.', markersize=1.5)
        ax1.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax1.axhline(mean_diff, color='green', linestyle='-', linewidth=1.5, alpha=0.7,
                   label=f'Mean = {mean_diff:.2f} ppm')
        ax1.fill_between(merged['timestamp'],
                        mean_diff - std_diff,
                        mean_diff + std_diff,
                        color='green', alpha=0.2, label=f'±1σ = {std_diff:.2f} ppm')
        
        ax1.set_ylabel('Difference (ppm)', fontsize=12)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_title(f'Difference: {test_name} - {reference_name}',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Format date tick labels on the timeseries panel
        ax1.tick_params(axis='x', rotation=30)
        
        # Panel 2: Histogram
        ax2 = fig.add_subplot(gs[1])
        ax2.hist(merged['diff'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', linewidth=1.5)
        ax2.axvline(mean_diff, color='green', linestyle='-', linewidth=1.5)
        ax2.set_xlabel('Difference (ppm)', fontsize=12)
        ax2.set_ylabel('Count', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filename = f"difference_{test_name}_vs_{reference_name}.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_co2_timeseries(
        self,
        data: 'Path | pd.DataFrame',
        sensor_name: str,
        period_label: Optional[str] = None,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot CO2 timeseries for a single sensor with summary statistics.
        
        Creates a timeseries of CO2 readings annotated with mean, std,
        min/max, and sample count. Works for both full datasets and
        monthly subsets.
        
        Args:
            data: Path to sensor CSV file, or a pre-loaded DataFrame
                  (must contain 'timestamp' and a recognised CO2 column)
            sensor_name: Sensor name for title and filename
            period_label: Optional period label (e.g., '2024_09') appended
                          to filename. If None, uses 'full'.
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object, or None if no CO2 data found
        """
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            df = pd.read_csv(data, parse_dates=['timestamp'])
        
        try:
            co2_col = self._detect_co2_column(df)
        except ValueError:
            self.logger.warning("No CO2 column in data for %s", sensor_name)
            return None
        
        co2 = df[['timestamp', co2_col]].dropna()
        
        if co2.empty:
            self.logger.warning("No valid CO2 data for %s", sensor_name)
            return None
        
        # Statistics
        vals = co2[co2_col]
        stats = {
            'mean': vals.mean(),
            'std': vals.std(),
            'min': vals.min(),
            'max': vals.max(),
            'n': len(vals),
        }
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 6))
        
        ax.plot(co2['timestamp'], vals,
                color='steelblue', alpha=0.8, linewidth=0.8,
                marker='.', markersize=2,
                label=sensor_name)
        
        # Mean line
        ax.axhline(stats['mean'], color='green', linestyle='-',
                   linewidth=1.5, alpha=0.7,
                   label=f"Mean = {stats['mean']:.1f} ppm")
        
        # +/- 1 std band
        ax.fill_between(
            co2['timestamp'],
            stats['mean'] - stats['std'],
            stats['mean'] + stats['std'],
            color='green', alpha=0.1,
            label=f"\u00b11\u03c3 = {stats['std']:.1f} ppm")
        
        # Stats annotation
        stats_text = (f"n = {stats['n']}\n"
                      f"Mean = {stats['mean']:.1f} ppm\n"
                      f"\u03c3 = {stats['std']:.1f} ppm\n"
                      f"Range = [{stats['min']:.0f}, {stats['max']:.0f}] ppm")
        ax.text(0.98, 0.95, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Styling
        title = f'{sensor_name}: CO\u2082 Timeseries'
        if period_label:
            title += f' ({period_label})'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('CO\u2082 (ppm)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            suffix = period_label if period_label else 'full'
            filename = f"{sensor_name}_co2_timeseries_{suffix}.png"
            self._save_figure(fig, filename)
        
        return fig