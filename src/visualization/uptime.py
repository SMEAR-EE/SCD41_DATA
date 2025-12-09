"""Uptime visualization tools

All uptime plots follow the same pattern:
1. Load uptime CSV
2. Calculate daily/monthly aggregates
3. Create matplotlib figure
4. Save with consistent naming
"""

from pathlib import Path
from typing import Dict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .base import BasePlotter


class UptimePlots(BasePlotter):
    """Generate uptime analysis plots"""
    
    def plot_timeseries(
        self,
        uptime_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot daily uptime percentage over time
        
        Args:
            uptime_csv: Path to uptime log CSV
            sensor_name: Sensor name for title
            save: If True, save to output_dir
        """
        df = pd.read_csv(uptime_csv)
        
        # Parse dates
        df['start'] = pd.to_datetime(df['start'], errors='coerce')
        df['date'] = df['start'].dt.floor('D')
        df['uptime_pct'] = df['uptime_ratio'] * 100
        
        # Drop invalid dates
        df = df.dropna(subset=['date'])
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Plot with markers
        ax.plot(df['date'], df['uptime_pct'], marker='o', linewidth=1.5, 
                markersize=4, color='steelblue', label='Daily Uptime')
        
        # Add 95% threshold line
        ax.axhline(95, color='red', linestyle='--', linewidth=1, 
                   alpha=0.7, label='95% Threshold')
        
        # Highlight low-uptime days
        low_uptime = df[df['uptime_pct'] < 95]
        if not low_uptime.empty:
            ax.scatter(low_uptime['date'], low_uptime['uptime_pct'],
                      color='red', s=50, zorder=5, alpha=0.7,
                      label=f'Low Uptime Days (n={len(low_uptime)})')
        
        # Styling
        ax.set_ylabel('Uptime (%)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title(f'{sensor_name}: Daily Uptime', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower left')
        
        # Format x-axis
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_uptime_timeseries.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_heatmap(
        self,
        uptime_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot uptime as monthly heatmap
        
        Args:
            uptime_csv: Path to uptime log CSV
            sensor_name: Sensor name for title
            save: If True, save to output_dir
        """
        df = pd.read_csv(uptime_csv)
        
        # Create pivot table (month x day)
        pivot = df.pivot_table(
            index='month',
            columns='day',
            values='uptime_ratio',
            aggfunc='mean'
        )
        
        # Create plot
        fig, ax = plt.subplots(figsize=(16, 8))
        
        sns.heatmap(
            pivot,
            cmap='RdYlGn',
            vmin=0,
            vmax=1,
            linewidths=0.5,
            cbar_kws={'label': 'Uptime Ratio'},
            ax=ax
        )
        
        ax.set_title(f'{sensor_name}: Uptime Heatmap', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Day of Month', fontsize=12)
        ax.set_ylabel('Month', fontsize=12)
        
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_uptime_heatmap.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_summary(
        self,
        uptime_csvs: Dict[str, Path],
        save: bool = True
    ) -> plt.Figure:
        """
        Multi-sensor uptime comparison
        
        Args:
            uptime_csvs: Dict of {sensor_name: uptime_csv_path}
            save: If True, save to output_dir
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        stats = []
        for sensor_name, csv_path in uptime_csvs.items():
            df = pd.read_csv(csv_path)
            stats.append({
                'sensor': sensor_name,
                'mean_uptime': df['uptime_ratio'].mean() * 100,
                'median_uptime': df['uptime_ratio'].median() * 100,
                'min_uptime': df['uptime_ratio'].min() * 100,
                'days_below_95': (df['uptime_ratio'] < 0.95).sum()
            })
        
        stats_df = pd.DataFrame(stats)
        
        # Bar chart of mean uptime
        ax1.bar(stats_df['sensor'], stats_df['mean_uptime'], 
                color='steelblue', alpha=0.8)
        ax1.axhline(95, color='red', linestyle='--', linewidth=1, alpha=0.7)
        ax1.set_ylabel('Mean Uptime (%)', fontsize=12)
        ax1.set_title('Average Uptime by Sensor', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, 105)
        ax1.grid(axis='y', alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Bar chart of days below 95%
        ax2.bar(stats_df['sensor'], stats_df['days_below_95'],
                color='coral', alpha=0.8)
        ax2.set_ylabel('Days Below 95% Uptime', fontsize=12)
        ax2.set_title('Low-Uptime Days by Sensor', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save:
            filename = "uptime_summary_all_sensors.png"
            self._save_figure(fig, filename)
        
        return fig