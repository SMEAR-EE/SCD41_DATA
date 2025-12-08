"""Visualization tools for sensor data analysis

All plots follow the same pattern:
1. Load data
2. Calculate stats
3. Create matplotlib figure
4. Save with consistent naming

"""

import logging
from pathlib import Path
from typing import Optional, List, Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec


class SensorVisualizer:
    """Generate publication-quality plots for sensor data"""
    
    def __init__(self, output_dir: Path = Path("output/plots")):
        """
        Args:
            output_dir: Where to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Set publication-quality defaults
        self._setup_style()
    
    def _setup_style(self):
        """Configure matplotlib for publication-quality plots"""
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams.update({
            'figure.dpi': 150,
            'savefig.dpi': 300,
            'font.size': 10,
            'axes.labelsize': 12,
            'axes.titlesize': 14,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.figsize': (12, 6)
        })
    
    # ============================================================
    # UPTIME PLOTS (from original)
    # ============================================================
    
    def plot_uptime_timeseries(
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
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    def plot_uptime_heatmap(
        self,
        uptime_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot uptime as monthly heatmap (from original)
        
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
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    def plot_uptime_summary(
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
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    # ============================================================
    # CO2 COMPARISON PLOTS (new - for validation)
    # ============================================================
    
    def plot_co2_timeseries(
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
        fig, ax = plt.subplots(figsize=(16, 8))
        
        for sensor_name, csv_path in data_csvs.items():
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            
            # Filter date range
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # Plot CO2 (use co2_mean if available, else co2)
            co2_col = 'co2_mean' if 'co2_mean' in df.columns else 'co2'
            
            ax.plot(df['timestamp'], df[co2_col], 
                   label=sensor_name, linewidth=1.5, alpha=0.8)
        
        ax.set_ylabel('CO₂ (ppm)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title('CO₂ Time Series Comparison', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            date_suffix = f"_{start_date}_to_{end_date}" if start_date else ""
            filename = f"co2_timeseries{date_suffix}.png"
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    def plot_co2_scatter(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str = "LGR Reference",
        test_name: str = "SCD41",
        save: bool = True
    ) -> plt.Figure:
        """
        Scatter plot: Reference vs Test sensor
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csv: Path to test sensor CSV
            reference_name: Name for reference sensor
            test_name: Name for test sensor
            save: If True, save to output_dir
        """
        # Load data
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        # Merge on timestamp
        ref_col = 'co2_dry_mean' if 'co2_dry_mean' in ref.columns else 'co2_mean'
        test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
        
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        )
        
        # Remove NaN
        merged = merged.dropna()
        
        # Calculate statistics
        r = np.corrcoef(merged[ref_col], merged[test_col])[0, 1]
        rmse = np.sqrt(np.mean((merged[ref_col] - merged[test_col])**2))
        bias = np.mean(merged[test_col] - merged[ref_col])
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 10))
        
        # Scatter plot
        ax.scatter(merged[ref_col], merged[test_col],
                  alpha=0.3, s=20, color='steelblue')
        
        # 1:1 line
        lims = [
            np.min([ax.get_xlim(), ax.get_ylim()]),
            np.max([ax.get_xlim(), ax.get_ylim()])
        ]
        ax.plot(lims, lims, 'k-', alpha=0.5, linewidth=2, label='1:1 Line')
        
        # Add stats text
        stats_text = f'R = {r:.3f}\nRMSE = {rmse:.2f} ppm\nBias = {bias:.2f} ppm\nn = {len(merged)}'
        ax.text(0.05, 0.95, stats_text,
               transform=ax.transAxes,
               fontsize=12,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_xlabel(f'{reference_name} CO₂ (ppm)', fontsize=12)
        ax.set_ylabel(f'{test_name} CO₂ (ppm)', fontsize=12)
        ax.set_title(f'{test_name} vs {reference_name}',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        if save:
            filename = f"co2_scatter_{test_name}_vs_{reference_name}.png"
            filename = filename.replace(' ', '_')
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    def plot_co2_difference(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str = "LGR",
        test_name: str = "SCD41",
        save: bool = True
    ) -> plt.Figure:
        """
        Plot difference (bias) over time
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csv: Path to test sensor CSV
            reference_name: Name for reference sensor
            test_name: Name for test sensor
            save: If True, save to output_dir
        """
        # Load and merge
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
        ref_col = 'co2_dry_mean' if 'co2_dry_mean' in ref.columns else 'co2_mean'
        test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
        
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        )
        
        merged['difference'] = merged[test_col] - merged[ref_col]
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
        
        # Time series of difference
        ax1.plot(merged['timestamp'], merged['difference'],
                linewidth=1, alpha=0.7, color='steelblue')
        ax1.axhline(0, color='black', linestyle='-', linewidth=1)
        ax1.axhline(merged['difference'].mean(), color='red',
                   linestyle='--', linewidth=1.5,
                   label=f'Mean Bias = {merged["difference"].mean():.2f} ppm')
        ax1.fill_between(merged['timestamp'],
                        merged['difference'].mean() - merged['difference'].std(),
                        merged['difference'].mean() + merged['difference'].std(),
                        alpha=0.2, color='red',
                        label=f'±1σ = {merged["difference"].std():.2f} ppm')
        ax1.set_ylabel('Difference (ppm)', fontsize=12)
        ax1.set_title(f'{test_name} - {reference_name} Bias Over Time',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Histogram of differences
        ax2.hist(merged['difference'], bins=50, color='steelblue',
                alpha=0.7, edgecolor='black')
        ax2.axvline(0, color='black', linestyle='-', linewidth=1)
        ax2.axvline(merged['difference'].mean(), color='red',
                   linestyle='--', linewidth=1.5)
        ax2.set_xlabel('Difference (ppm)', fontsize=12)
        ax2.set_ylabel('Frequency', fontsize=12)
        ax2.set_title('Bias Distribution', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            filename = f"co2_difference_{test_name}_vs_{reference_name}.png"
            filename = filename.replace(' ', '_')
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    # ============================================================
    # ADVANCED PLOTS (extensible base for Taylor diagrams, etc.)
    # ============================================================
    
    def plot_taylor_diagram(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "LGR Reference",
        save: bool = True
    ) -> plt.Figure:
        """
        Taylor diagram for multi-sensor comparison
        
        Shows correlation, RMSE, and std deviation on single plot.
        Extensible base - you can enhance this!
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path} for test sensors
            reference_name: Name for reference sensor
            save: If True, save to output_dir
        
        Note: This is a simplified Taylor diagram. For publication-quality,
              consider using the `skill_metrics` package.
        """
        # Load reference
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = 'co2_dry_mean' if 'co2_dry_mean' in ref.columns else 'co2_mean'
        
        # Calculate stats for each test sensor
        stats = []
        for test_name, test_csv in test_csvs.items():
            test = pd.read_csv(test_csv, parse_dates=['timestamp'])
            test_col = 'co2_mean' if 'co2_mean' in test.columns else 'co2'
            
            merged = pd.merge(
                ref[['timestamp', ref_col]],
                test[['timestamp', test_col]],
                on='timestamp',
                how='inner'
            ).dropna()
            
            if len(merged) > 0:
                corr = np.corrcoef(merged[ref_col], merged[test_col])[0, 1]
                std_ratio = merged[test_col].std() / merged[ref_col].std()
                rmse = np.sqrt(np.mean((merged[ref_col] - merged[test_col])**2))
                
                stats.append({
                    'name': test_name,
                    'correlation': corr,
                    'std_ratio': std_ratio,
                    'rmse': rmse
                })
        
        # Create polar plot (simplified Taylor diagram)
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='polar')
        
        # Plot each sensor
        colors = plt.cm.tab10(np.linspace(0, 1, len(stats)))
        
        for i, stat in enumerate(stats):
            theta = np.arccos(stat['correlation'])
            r = stat['std_ratio']
            
            ax.plot(theta, r, 'o', markersize=12, color=colors[i],
                   label=f"{stat['name']} (RMSE={stat['rmse']:.1f})")
        
        # Add reference point
        ax.plot(0, 1, '*', markersize=20, color='red',
               label=reference_name, zorder=10)
        
        # Styling
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_ylim(0, 2)
        ax.set_xlabel('Std Deviation Ratio', fontsize=12)
        ax.set_title('Taylor Diagram: Multi-Sensor Comparison',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        
        # Add correlation labels
        corr_ticks = [0.9, 0.95, 0.99]
        corr_angles = [np.arccos(c) for c in corr_ticks]
        ax.set_xticks(corr_angles)
        ax.set_xticklabels([f'{c:.2f}' for c in corr_ticks])
        
        plt.tight_layout()
        
        if save:
            filename = "taylor_diagram_multi_sensor.png"
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        self.logger.info(
            "Note: For publication-quality Taylor diagrams, "
            "consider using the 'skill_metrics' package"
        )
        
        return fig
    
    # ============================================================
    # QC ANALYSIS PLOTS (new - data quality)
    # ============================================================
    
    def plot_qc_summary(
        self,
        data_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Visualize QC flag distribution
        
        Args:
            data_csv: Path to processed sensor CSV
            sensor_name: Sensor name for title
            save: If True, save to output_dir
        """
        df = pd.read_csv(data_csv)
        
        # Find QC columns
        qc_cols = [c for c in df.columns if c.endswith('_qc')]
        
        if not qc_cols:
            self.logger.warning(f"No QC columns found in {data_csv}")
            return None
        
        # Create subplots
        n_cols = len(qc_cols)
        fig, axes = plt.subplots(1, n_cols, figsize=(6 * n_cols, 5))
        
        if n_cols == 1:
            axes = [axes]
        
        for ax, qc_col in zip(axes, qc_cols):
            var_name = qc_col.replace('_qc', '').upper()
            
            # Count QC flags
            qc_counts = df[qc_col].value_counts()
            
            # Bar plot
            qc_counts.plot(kind='bar', ax=ax, color='steelblue', alpha=0.8)
            ax.set_title(f'{var_name} QC Flags', fontsize=12, fontweight='bold')
            ax.set_ylabel('Count', fontsize=10)
            ax.set_xlabel('QC Flag', fontsize=10)
            ax.grid(axis='y', alpha=0.3)
            
            # Add percentage labels
            total = qc_counts.sum()
            for i, (flag, count) in enumerate(qc_counts.items()):
                pct = 100 * count / total
                ax.text(i, count, f'{pct:.1f}%',
                       ha='center', va='bottom', fontsize=9)
        
        fig.suptitle(f'{sensor_name}: Quality Control Summary',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_qc_summary.png"
            fig.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
            self.logger.info(f"Saved: {filename}")
        
        return fig
    
    # ============================================================
    # PLACEHOLDER FOR ADDITIONAL ANALYSES
    # some ideas for future plots... 
    # ============================================================
    def plot_diurnal_cycle(self):
        """Average CO2 by hour of day"""
        pass
    
    def plot_vertical_gradient(self):
        """2m vs 30m concentration gradient"""
        pass
    
    def plot_meteorological_correlation(self):
        """CO2 vs temperature, wind, etc."""
        pass
    
    def plot_spectral_analysis(self):
        """FFT / power spectrum"""
        pass
    
    def plot_skill_score(self):
        """Full Taylor diagram with skill_metrics package"""
        pass


# ============================================================
# CONVENIENCE FUNCTION: Generate All Standard Plots
# ============================================================

def generate_all_plots(
    individual_dir: Path,
    sensor_names: List[str],
    output_dir: Path = Path("output/plots")
):
    """
    Generate all standard plots for processed data
    
    Args:
        individual_dir: Path to output/individual/ directory
        sensor_names: List of sensor names to plot
        output_dir: Where to save plots
    
    Example:
        generate_all_plots(
            Path("output/individual"),
            ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"]
        )
    """
    viz = SensorVisualizer(output_dir)
    
    print("Generating plots...")
    
    # 1. Uptime plots for each sensor
    uptime_csvs = {}
    data_csvs = {}
    
    for sensor in sensor_names:
        uptime_csv = individual_dir / f"{sensor}_uptime.csv"
        data_csv = individual_dir / f"{sensor}_10min.csv"
        
        if uptime_csv.exists():
            print(f"  - {sensor}: Uptime timeseries")
            viz.plot_uptime_timeseries(uptime_csv, sensor)
            
            print(f"  - {sensor}: Uptime heatmap")
            viz.plot_uptime_heatmap(uptime_csv, sensor)
            
            uptime_csvs[sensor] = uptime_csv
        
        if data_csv.exists():
            print(f"  - {sensor}: QC summary")
            viz.plot_qc_summary(data_csv, sensor)
            
            data_csvs[sensor] = data_csv
    
    # 2. Multi-sensor uptime comparison
    if len(uptime_csvs) > 1:
        print("  - Multi-sensor uptime summary")
        viz.plot_uptime_summary(uptime_csvs)
    
    # 3. CO2 timeseries comparison
    if len(data_csvs) > 1:
        print("  - CO2 timeseries comparison")
        viz.plot_co2_timeseries(data_csvs)
    
    # 4. Validation plots (SCD41 vs LGR)
    lgr_csv = individual_dir / "LGR_30M_10min.csv"
    if lgr_csv.exists():
        for sensor in ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C"]:
            test_csv = individual_dir / f"{sensor}_10min.csv"
            if test_csv.exists():
                print(f"  - {sensor} vs LGR: Scatter plot")
                viz.plot_co2_scatter(lgr_csv, test_csv, "LGR", sensor)
                
                print(f"  - {sensor} vs LGR: Difference plot")
                viz.plot_co2_difference(lgr_csv, test_csv, "LGR", sensor)
        
        # Taylor diagram
        scd41_csvs = {s: individual_dir / f"{s}_10min.csv" 
                      for s in ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C"]
                      if (individual_dir / f"{s}_10min.csv").exists()}
        
        if len(scd41_csvs) > 1:
            print("  - Taylor diagram")
            viz.plot_taylor_diagram(lgr_csv, scd41_csvs)
            print(f"\n✓ All plots saved to: {output_dir}")
    