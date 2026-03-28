"""Quality control visualization tools

Analyze and visualize QC flag distributions and patterns.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from .base_plotter import BasePlotter
import json

class QualityControlPlots(BasePlotter):
    """Generate QC analysis plots"""
    
    def plot_qc_summary(
        self,
        data_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Visualize QC flag distribution for all variables.
        
        Creates a multi-panel bar chart showing the count and percentage
        of each QC flag for each measured variable (CO2, temperature, humidity, etc.).
        Useful for identifying systematic data quality issues.
        Uses coverage JSON (from pipeline) for MISSING count when available,
        falls back to timestamp-based estimation otherwise.
        
        Args:
            data_csv: Path to processed sensor 10min CSV file
            sensor_name: Sensor name for plot title and filename
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object with subplots for each variable, or None
            if no QC columns are found in the CSV
        """
        df = pd.read_csv(data_csv)
        n_actual = len(df)
        
        # Try loading coverage summary from sensor root dir
        coverage_json = data_csv.parent.parent / f"{sensor_name}_coverage.json"
        if coverage_json.exists():
            self.logger.info(f"Using coverage JSON for {sensor_name}")
            with open(coverage_json) as f:
                coverage = json.load(f)
            n_expected = coverage['expected_records_10min']
        else:
            # Fallback: estimate from timestamp range
            self.logger.warning(f"No coverage JSON for {sensor_name}, estimating from timestamps")
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
            expected_range = pd.date_range(df['timestamp'].min(), df['timestamp'].max(), freq='10min')
            n_expected = len(expected_range)
    
        n_missing = n_expected - n_actual
        
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
            
            # Count existing flags, then add missing records
            qc_counts = df[qc_col].value_counts().to_dict()
            if n_missing > 0:
                qc_counts['MISSING'] = n_missing
        
            qc_series = pd.Series(qc_counts).sort_values(ascending=False)
            
            # paint MISSING readings differently
            colors = ['coral' if k == 'MISSING' else 'steelblue' for k in qc_series.index]
            
            qc_series.plot(kind='bar', ax=ax, color=colors, alpha=0.8)
            
            total = n_expected # ... percentage labels use n_expected as denominator
            for i, (flag, count) in enumerate(qc_series.items()):
                pct = 100 * count / total
                ax.text(i, count, f'{pct:.1f}%', ha='center', va='bottom', fontsize=9)
            
            ax.set_title(f'{var_name} QC Flags', fontsize=12, fontweight='bold')
            ax.set_ylabel('Count', fontsize=10)
            ax.set_xlabel('QC Flag', fontsize=10)
            ax.grid(axis='y', alpha=0.3)
        
        fig.suptitle(f'{sensor_name}: Quality Control Summary',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_qc_summary.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_qc_multi_sensor(
        self,
        data_csvs: dict,
        save: bool = True,
    ) -> plt.Figure:
        """Grouped bar chart of CO₂ QC flag distribution across all sensors.

        Args:
            data_csvs: Dict mapping sensor names to 10min CSV paths.
            save: If True, save to output_dir (default: True).

        Returns:
            matplotlib Figure object.
        """
        from collections import OrderedDict
        import numpy as np

        DISPLAY = {
            'CO2_SCT1_2M': 'SCD41 2m',
            'CO2_30M_A': 'SCD41 A\n(30m)',
            'CO2_30M_B': 'SCD41 B\n(30m)',
            'CO2_30M_C': 'SCD41 C\n(30m)',
            'LGR_30M': 'LGR\n(30m)',
        }
        FLAG_COLOURS = {
            'OK': '#4c9f38',
            'BELOW_RANGE': '#e15759',
            'ABOVE_RANGE': '#f28e2b',
            'NO_DATA': '#bab0ab',
        }

        sensor_qc = OrderedDict()
        for name, csv_path in data_csvs.items():
            df = pd.read_csv(csv_path,
                             usecols=lambda c: c == 'co2_qc' or c.endswith('_co2_qc'))
            qc_col = [c for c in df.columns if 'co2' in c.lower() and c.endswith('_qc')]
            if not qc_col:
                continue
            sensor_qc[name] = df[qc_col[0]].value_counts().to_dict()

        all_flags = sorted({f for counts in sensor_qc.values() for f in counts})
        sensor_names = list(sensor_qc.keys())
        display_names = [DISPLAY.get(s, s) for s in sensor_names]
        totals = {s: sum(c.values()) for s, c in sensor_qc.items()}

        max_ok = max(sensor_qc[s].get('OK', 0) for s in sensor_names)
        min_flagged = min(
            (c for s in sensor_names for f, c in sensor_qc[s].items() if f != 'OK'),
            default=max_ok)
        use_log = (max_ok / max(min_flagged, 1)) > 50

        n_sensors = len(sensor_names)
        n_flags = len(all_flags)
        x = np.arange(n_sensors)
        bar_w = 0.8 / n_flags

        fig, ax = plt.subplots(figsize=(10, 5))
        for j, flag in enumerate(all_flags):
            counts = [sensor_qc[s].get(flag, 0) for s in sensor_names]
            colour = FLAG_COLOURS.get(flag, '#76b7b2')
            offset = (j - (n_flags - 1) / 2) * bar_w
            ax.bar(x + offset, counts, bar_w * 0.9, label=flag,
                   color=colour, edgecolor='white', linewidth=0.5)

        if use_log:
            ax.set_yscale('log')
            ax.set_ylabel('Record count (log scale)', fontsize=11)
        else:
            ax.set_ylabel('Record count', fontsize=11)

        y_top = ax.get_ylim()[1]
        for i, s in enumerate(sensor_names):
            ax.text(i, y_top, f'n={totals[s]:,}',
                    ha='center', va='bottom', fontsize=9, fontweight='bold')
        ax.set_ylim(top=y_top * (4 if use_log else 1.15))

        ax.set_xticks(x)
        ax.set_xticklabels(display_names, fontsize=10)
        ax.set_title('CO₂ QC Flag Distribution — All Sensors',
                     fontsize=13, fontweight='bold')
        ax.legend(title='QC Flag', fontsize=9, title_fontsize=10, loc='upper right')
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()

        if save:
            self._save_figure(fig, "qc_flag_distribution_all_sensors.png")
        return fig