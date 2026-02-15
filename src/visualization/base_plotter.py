"""Base visualization configuration and utilities

Provides consistent matplotlib styling for all plot modules.
"""

import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


class BasePlotter:
    """Base class for all visualization modules
    
    Provides:
    - Consistent matplotlib styling
    - Output directory management
    - Logging setup
    - CO2 column detection across sensor types
    """
    
    # Column names in priority order (most specific first)
    CO2_COLUMN_NAMES = [
        'CO2_dry_mean', 'co2_dry_mean',
        'CO2_dry', 'co2_dry',
        'co2_mean', 'CO2_mean',
        'co2', 'CO2',
    ]
    
    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: Where to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set publication-quality defaults
        self._setup_style()
    
    def _detect_co2_column(self, df: pd.DataFrame) -> str:
        """Detect CO2 column name across sensor types.
        
        Checks a priority-ordered list of known column names
        used by different parsers (SCD41: co2_mean, LGR: CO2_dry_mean, etc.).
        
        Args:
            df: DataFrame to inspect
            
        Returns:
            Column name string
            
        Raises:
            ValueError: If no recognised CO2 column is found
        """
        for col in self.CO2_COLUMN_NAMES:
            if col in df.columns:
                return col
        raise ValueError(
            f"No recognised CO2 column found. "
            f"Available columns: {list(df.columns)}"
        )
    
    def _setup_style(self):
        """Configure matplotlib for publication-quality plots"""
        # plt.style.use('seaborn-v0_8-darkgrid')
        plt.style.use('ggplot')
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
    
    def _save_figure(self, fig: plt.Figure, filename: str):
        """Save figure with consistent settings
        
        Args:
            fig: Matplotlib figure to save
            filename: Output filename (with extension)
        """
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        self.logger.info(f"Saved: {filename}")