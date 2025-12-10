"""Single-day data processor"""
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import pandas as pd
import numpy as np

from .parsers import SCD41Parser, LGRParser
from .uptime import UptimeCalculator


class DayProcessor:
    """Process single day of sensor data"""
    
    def __init__(self, config):
        self.config = config
        self.uptime_calc = UptimeCalculator(config)
        self.logger = logging.getLogger(__name__)
        
        # Initialize parser based on sensor type
        if config.sensor_type == 'scd41':
            self.parser = SCD41Parser(config, sensor_id=config.sensor_id)
        elif config.sensor_type == 'lgr_csv':
            self.parser = LGRParser(config)
        else:
            raise ValueError(f"Unknown sensor type: {config.sensor_type}")
    
    def process(
        self,
        files: List[Path],
        date_key: Tuple[int, int, int]
    ) -> Optional[Tuple[pd.DataFrame, Dict]]:
        """
        Process day's files and return 10-min aggregated data
        
        Args:
            files: List of file paths for this day
            date_key: (year, month, day) tuple
        
        Returns:
            Tuple of (aggregated_df, uptime_stats) or None
        """
        year, month, day = date_key
        self.logger.info(
            f"Processing {year}-{month:02d}-{day:02d} "
            f"({len(files)} files)"
        )
        
        # Parse all files
        dfs = []
        for f in files:
            df = self.parser.parse_file(f)
            if df is not None:
                dfs.append(df)
        
        if not dfs:
            self.logger.warning(
                f"No valid data for {year}-{month:02d}-{day:02d}"
            )
            return None
        
        # Combine and sort
        df_raw = pd.concat(dfs, ignore_index=True)
        df_raw = df_raw.sort_values('timestamp').set_index('timestamp')
        
        # Remove duplicates
        initial_count = len(df_raw)
        df_raw = df_raw[~df_raw.index.duplicated(keep='last')]
        if len(df_raw) < initial_count:
            self.logger.info(
                f"Removed {initial_count - len(df_raw)} duplicate timestamps"
            )
        
        # CRITICAL FIX: Filter to only measurements from THIS day before resampling
        # This prevents day-boundary overlap duplicates when files contain data
        # from adjacent days (common when files are timestamped by creation time)
        day_start = pd.Timestamp(year, month, day)
        day_end = day_start + pd.Timedelta(days=1)
        df_day = df_raw[(df_raw.index >= day_start) & (df_raw.index < day_end)]
        
        if len(df_day) == 0:
            self.logger.warning(
                f"No data in date range for {year}-{month:02d}-{day:02d}"
            )
            return None
        
        if len(df_day) < len(df_raw):
            self.logger.debug(
                f"Filtered {len(df_raw) - len(df_day)} measurements outside day boundary"
            )
        
        # Calculate uptime on the filtered day data
        uptime_stats = self.uptime_calc.calculate(df_day)
        uptime_stats.update({'year': year, 'month': month, 'day': day})
        
        # Log low uptime
        if uptime_stats['uptime_ratio'] < 0.95:
            self.logger.warning(
                f"⚠️ Low uptime: {uptime_stats['uptime_ratio']:.1%} "
                f"({uptime_stats['num_gaps']} gaps, "
                f"max {uptime_stats['max_gap_minutes']:.0f} min)"
            )
        
        # 10-minute resampling with epoch origin (time sync!)
        df_10min = self._resample_10min(df_day)
        
        self.logger.info(
            f"✓ {year}-{month:02d}-{day:02d}: "
            f"{len(df_day)} raw → {len(df_10min)} 10-min samples "
            f"(uptime: {uptime_stats['uptime_ratio']:.1%})"
        )
        
        return df_10min, uptime_stats
    
    def _resample_10min(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample to 10-min intervals with proper uncertainty propagation
        
        Uses epoch origin for time synchronization across sensors
        """
        # Separate numeric and QC columns
        numeric_cols = [c for c in df.columns if not c.endswith('_qc')]
        qc_cols = [c for c in df.columns if c.endswith('_qc')]
        
        # Resample numeric columns
        agg_dict = {}
        for col in numeric_cols:
            if col.endswith('_sd'):
                # Propagate uncertainty: sqrt(sum(sd^2)) / n
                agg_dict[col] = lambda x: np.sqrt(np.sum(x**2)) / len(x) if len(x) > 0 else np.nan
            else:
                agg_dict[col] = ['mean', 'std', 'count']
        
        df_10min = df[numeric_cols].resample('10min', origin='epoch').agg(agg_dict)
        
        # Flatten multi-level columns
        df_10min.columns = ['_'.join(col).strip('_') for col in df_10min.columns.values]
        
        # Add QC flag summary (most common flag per window)
        for qc_col in qc_cols:
            df_10min[qc_col] = df[qc_col].resample('10min', origin='epoch').apply(
                lambda x: x.mode()[0] if len(x) > 0 else 'NO_DATA'
            )
        
        return df_10min