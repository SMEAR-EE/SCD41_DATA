"""Quality control visualization tools

Analyze and visualize QC flag distributions and patterns.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from .base_plotter import BasePlotter


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
        
        Args:
            data_csv: Path to processed sensor 10min CSV file
            sensor_name: Sensor name for plot title and filename
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object with subplots for each variable, or None
            if no QC columns are found in the CSV
        """
        df = pd.read_csv(data_csv)
        
        # TODO (v0.2.0): MISSING flag injection should move upstream to
        # DayProcessor._resample_10min() in processor.py. After resampling,
        # reindex against the full day range (00:00–23:50 at 10min freq)
        # and tag empty QC slots as 'MISSING'. Once the pipeline CSVs
        # contain MISSING natively, remove the expected-range calculation
        # below and simplify back to just counting flags from the CSV.
        # See also: v0.3.0 note on merged uptime parquet consolidation.
        
        # Calculate expected vs actual records
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        expected_range = pd.date_range(df['timestamp'].min(), df['timestamp'].max(), freq='10min')
        n_expected = len(expected_range)
        n_actual = len(df)
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