"""Taylor diagram visualization

NOTE: This module is currently not working correctly.
      Placeholder for future implementation.

For publication-quality Taylor diagrams, consider using:
- skill_metrics package: https://github.com/PeterRochford/SkillMetrics
- taylorDiagram package
"""

from pathlib import Path
from typing import Dict
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .base import BasePlotter


class TaylorDiagram(BasePlotter):
    """Generate Taylor diagrams for multi-sensor comparison
    
    WARNING: Current implementation needs fixing.
             Use at your own risk.
    """
    
    def plot(
        self,
        reference_csv: Path,
        test_csvs: Dict[str, Path],
        reference_name: str = "Reference",
        save: bool = True
    ) -> plt.Figure:
        """
        Create Taylor diagram comparing multiple sensors to reference
        
        Taylor diagrams show three statistics simultaneously:
        - Correlation (angular position)
        - Standard deviation ratio (radial distance)
        - RMSE (distance from reference point)
        
        Args:
            reference_csv: Path to reference sensor CSV
            test_csvs: Dict of {sensor_name: csv_path}
            reference_name: Name of reference sensor
            save: If True, save to output_dir
            
        Returns:
            Matplotlib figure (but probably broken)
        """
        # Load reference
        ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref_col = 'co2_mean' if 'co2_mean' in ref.columns else 'co2'
        
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
        # TODO: This needs proper Taylor diagram implementation
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
            self._save_figure(fig, filename)
        
        self.logger.warning(
            "Taylor diagram implementation needs fixing. "
            "Consider using 'skill_metrics' package for publication-quality diagrams."
        )
        
        return fig