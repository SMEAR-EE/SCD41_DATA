"""Uptime calculation for sensor data"""
import logging
from typing import Dict
import numpy as np
import pandas as pd


class UptimeCalculator:
    """Calculate sensor uptime with multiple metrics"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Compute uptime metrics
        
        Args:
            df: DataFrame with DatetimeIndex
        
        Returns:
            Dictionary with uptime metrics including QC summary
        """
        if len(df) < 2:
            return self._empty_result()
        
        ts = df.index.to_series().sort_values()
        dt = ts.diff().dt.total_seconds().dropna()
        
        # Detect actual sampling interval
        detected_interval = float(dt.median())
        
        # Warn if unexpected
        expected = self.config.expected_interval
        if not (expected * 0.9 <= detected_interval <= expected * 1.1):
            self.logger.warning(
                f"Unexpected sample interval: {detected_interval:.1f}s "
                f"(expected ~{expected}s)"
            )
        
        # Gap detection
        gap_threshold = 2 * expected
        gaps = dt[dt > gap_threshold]
        
        # Time-based uptime
        total_time = (ts.iloc[-1] - ts.iloc[0]).total_seconds()
        downtime = float(gaps.sum()) if len(gaps) > 0 else 0.0
        uptime_ratio = (total_time - downtime) / total_time if total_time > 0 else 0.0
        
        # likely uptime calc bug ~here~ for LGR data

        # Sample-based uptime
        expected_samples = total_time / expected
        sample_ratio = len(df) / expected_samples if expected_samples > 0 else 0.0
        
        # QC summary
        qc_summary = self._compute_qc_summary(df)
        
        return {
            'start': ts.iloc[0],
            'end': ts.iloc[-1],
            'uptime_ratio': float(uptime_ratio),
            'sample_ratio': float(sample_ratio),
            'num_gaps': int(len(gaps)),
            'max_gap_minutes': float(gaps.max() / 60) if len(gaps) > 0 else 0.0,
            'detected_interval': detected_interval,
            'total_samples': len(df),
            'expected_samples': int(expected_samples),
            **qc_summary
        }
    
    def _compute_qc_summary(self, df: pd.DataFrame) -> Dict:
        """Compute QC flag statistics"""
        qc_cols = [c for c in df.columns if c.endswith('_qc')]
        
        summary = {}
        for col in qc_cols:
            var_name = col.replace('_qc', '')
            summary[f'qc_{var_name}_ok'] = int((df[col] == 'OK').sum())
            summary[f'qc_{var_name}_flagged'] = int((df[col] != 'OK').sum())
        
        return summary
    
    def _empty_result(self) -> Dict:
        """Return empty result for invalid data"""
        return {
            'start': pd.NaT,
            'end': pd.NaT,
            'uptime_ratio': 0.0,
            'sample_ratio': 0.0,
            'num_gaps': 0,
            'max_gap_minutes': 0.0,
            'detected_interval': np.nan,
            'total_samples': 0,
            'expected_samples': 0
        }