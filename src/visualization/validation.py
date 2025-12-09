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
from .base import BasePlotter


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
        Plot CO2 timeseries for multiple sensors
        
        Args:
            data_csvs: Dict of {sensor_name: csv_path}
            start_date: Start date (YYYY-MM-DD) or None for all
            end_date: End date (YYYY-MM-DD) or None for all
            save: If True, save to output_dir
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
            co2_col = 'co2_mean' if 'co2_mean' in df.columns else 'co2'
            
            # Plot
            ax.plot(df['timestamp'], df[co2_col], label=sensor_name, alpha=0.7)
        
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
        Scatter plot: reference vs test sensor
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csv: Path to test sensor CSV
            reference_name: Reference sensor name (e.g., "LGR")
            test_name: Test sensor name (e.g., "CO2_30M_1")
            save: If True, save to output_dir
        """
        # Load data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        # Get CO2 columns
        ref_col = 'co2_mean' if 'co2_mean' in ref.columns else 'co2'
        test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
        
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
        Plot difference (test - reference) over time
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csv: Path to test sensor CSV
            reference_name: Reference sensor name
            test_name: Test sensor name
            save: If True, save to output_dir
        """
        # Load data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        # Get CO2 columns
        ref_col = 'co2_mean' if 'co2_mean' in ref.columns else 'co2'
        test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
        
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
                color='steelblue', alpha=0.7, linewidth=0.8)
        ax1.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax1.axhline(mean_diff, color='green', linestyle='-', linewidth=1.5, alpha=0.7,
                   label=f'Mean = {mean_diff:.2f} ppm')
        ax1.fill_between(merged['timestamp'],
                        mean_diff - std_diff,
                        mean_diff + std_diff,
                        color='green', alpha=0.2, label=f'±1σ = {std_diff:.2f} ppm')
        
        ax1.set_ylabel('Difference (ppm)', fontsize=12)
        ax1.set_title(f'Difference: {test_name} - {reference_name}',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Panel 2: Histogram
        ax2 = fig.add_subplot(gs[1])
        ax2.hist(merged['diff'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', linewidth=1.5)
        ax2.axvline(mean_diff, color='green', linestyle='-', linewidth=1.5)
        ax2.set_xlabel('Difference (ppm)', fontsize=12)
        ax2.set_ylabel('Count', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            filename = f"difference_{test_name}_vs_{reference_name}.png"
            self._save_figure(fig, filename)
        
        return fig