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
    
    def __init__(self, output_dir: Path, close_after_save: bool = False):
        """
        Initialise the plotter and apply publication-quality style defaults.

        Creates the output directory if it does not already exist, configures
        matplotlib with consistent rcParams, and sets up a class-level logger
        named after the concrete subclass.

        Args:
            output_dir: Directory in which to save plot files.  Created
                        automatically (including any parent directories) if it
                        does not exist.
            close_after_save: If True, close each figure immediately after
                              saving to suppress inline display in Jupyter
                              notebooks (default: False).

        Returns:
            None
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.close_after_save = close_after_save
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
        plt.style.use('ggplot') # has subscript support in fonts
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
    
    def _apply_qc_filter(self, df: pd.DataFrame, co2_col: str = None) -> pd.DataFrame:
        """Drop rows where the CO2 QC flag is not OK.

        Looks for a QC column that corresponds to the CO2 measurement:
        - In individual sensor CSVs: ``co2_qc``
        - In merged CSVs: ``{prefix}_co2_qc`` derived from *co2_col*

        Args:
            df: DataFrame to filter (not modified in place).
            co2_col: CO2 value column name.  When provided the method
                     derives the QC column as ``co2_col`` with
                     ``_mean`` stripped and ``_qc`` appended, falling
                     back to the bare ``co2_qc`` column.

        Returns:
            Filtered copy of *df* containing only rows with ``OK`` QC.
        """
        # Candidate QC column names in priority order
        candidates = []
        if co2_col:
            # e.g. co2_sct1_2m_co2_mean -> co2_sct1_2m_co2_qc
            base = co2_col.replace('_mean', '').replace('_dry', '')
            candidates.append(f"{base}_qc")
        candidates.extend(['co2_qc', 'CO2_qc'])

        for qc_col in candidates:
            if qc_col in df.columns:
                before = len(df)
                df = df[df[qc_col] == 'OK'].copy()
                dropped = before - len(df)
                if dropped:
                    self.logger.debug("QC filter (%s): dropped %d / %d rows",
                                      qc_col, dropped, before)
                return df

        # No QC column found — return unmodified
        return df

    @staticmethod
    def _break_gaps(df: pd.DataFrame, time_col: str = 'timestamp',
                    max_gap_minutes: float = 15.0) -> pd.DataFrame:
        """Insert NaN sentinel rows at timestamp gaps so plot lines break.

        Any gap between consecutive timestamps exceeding *max_gap_minutes*
        triggers a single NaN row, preventing matplotlib from drawing a
        line across the gap.

        Args:
            df: DataFrame sorted by *time_col*.
            time_col: Name of the datetime column.
            max_gap_minutes: Threshold in minutes above which a break is
                             inserted (default: 15.0).

        Returns:
            New DataFrame with NaN break rows inserted.
        """
        if len(df) < 2:
            return df
        dt = df[time_col].diff()
        gap_mask = dt > pd.Timedelta(minutes=max_gap_minutes)
        if not gap_mask.any():
            return df

        parts = []
        prev = 0
        for idx in df.index[gap_mask]:
            pos = df.index.get_loc(idx)
            parts.append(df.iloc[prev:pos])
            # Single NaN row at the midpoint of the gap
            mid_time = df[time_col].iloc[pos - 1] + (df[time_col].iloc[pos] - df[time_col].iloc[pos - 1]) / 2
            nan_row = pd.DataFrame({c: [pd.NaT if c == time_col else float('nan')]
                                    for c in df.columns})
            nan_row[time_col] = mid_time
            parts.append(nan_row)
            prev = pos
        parts.append(df.iloc[prev:])
        return pd.concat(parts, ignore_index=True)

    def _save_figure(self, fig: plt.Figure, filename: str):
        """Save figure with consistent settings
        
        Args:
            fig: Matplotlib figure to save
            filename: Output filename (with extension)
        """
        filepath = self.output_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches='tight')
        self.logger.info(f"Saved: {filename}")
        if self.close_after_save:
            plt.close(fig)