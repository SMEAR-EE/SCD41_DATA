"""Base visualization configuration and utilities

Provides consistent matplotlib styling for all plot modules.
"""

import logging
from pathlib import Path
import matplotlib.pyplot as plt


class BasePlotter:
    """Base class for all visualization modules
    
    Provides:
    - Consistent matplotlib styling
    - Output directory management
    - Logging setup
    """
    
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
    
    def _save_figure(self, fig: plt.Figure, filename: str):
        """Save figure with consistent settings
        
        Args:
            fig: Matplotlib figure to save
            filename: Output filename (with extension)
        """
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        self.logger.info(f"Saved: {filename}")