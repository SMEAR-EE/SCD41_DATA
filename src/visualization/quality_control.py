"""Quality control visualization tools

Analyze and visualize QC flag distributions and patterns.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from .base import BasePlotter


class QualityControlPlots(BasePlotter):
    """Generate QC analysis plots"""
    
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
            self._save_figure(fig, filename)
        
        return fig