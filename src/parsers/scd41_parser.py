"""Parser for SCD41 NodeRED JSON files"""
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from .base_parser import BaseSensorParser


class SCD41Parser(BaseSensorParser):
    """Parser for NodeRED JSON format from SCD41 sensors"""
    
    def __init__(self, config, sensor_id: Optional[str] = None):
        """
        Args:
            config: SensorConfig object
            sensor_id: 'A', 'B', 'C' for 30m sensors, None for 2m sensor
        """
        self.config = config
        self.sensor_id = sensor_id
        self.logger = logging.getLogger(__name__)
    
    def get_file_pattern(self) -> str:
        """Return glob pattern based on sensor_id"""
        if self.sensor_id:
            return f"SCD41_{self.sensor_id}.json-*"
        else:
            return "SCD41.json-*"
    
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Parse NodeRED JSON file"""
        rows = []
        malformed_count = 0
        
        try:
            with open(file_path, 'r', errors='ignore') as fh:
                for line_num, line in enumerate(fh, 1):
                    raw = line.strip()
                    if not raw or '\x00' in raw:
                        continue
                    
                    try:
                        entry = json.loads(raw)
                        ts = self._parse_timestamp(entry['time'])
                        if ts is None:
                            continue
                        
                        rows.append({
                            'timestamp': ts,
                            'co2': entry.get('co2', np.nan),
                            'temp': entry.get('temp', np.nan),
                            'humidity': entry.get('humidity', np.nan)
                        })
                    
                    except (json.JSONDecodeError, KeyError) as e:
                        malformed_count += 1
                        if malformed_count <= 5:
                            self.logger.warning(
                                f"{file_path.name}:{line_num} - {type(e).__name__}"
                            )
        
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return None
        
        if malformed_count > 0:
            self.logger.info(
                f"{file_path.name}: {malformed_count} malformed lines skipped"
            )
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows).sort_values('timestamp')
        return self.add_qc_flags(df)
    
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract from:
        - SCD41.json-2025-11-14T14-48-28.122Z (2m sensor)
        - SCD41_A.json-2025-11-14T14-48-28.122Z (30m sensor)
        """
        if self.sensor_id:
            pattern = re.compile(
                rf"SCD41_{self.sensor_id}\.json-(\d{{4}})-(\d{{2}})-(\d{{2}})T"
                rf"(\d{{2}})-(\d{{2}})-(\d{{2}}\.\d+)Z"
            )
        else:
            pattern = re.compile(
                r"SCD41\.json-(\d{4})-(\d{2})-(\d{2})T"
                r"(\d{2})-(\d{2})-(\d{2}\.\d+)Z"
            )
        
        m = pattern.match(filename)
        if not m:
            return None
        
        Y, M, D, h, m_val, s = m.groups()
        return datetime(int(Y), int(M), int(D), int(h), int(m_val), int(float(s)))
    
    def _parse_timestamp(self, time_str: str) -> Optional[pd.Timestamp]:
        """Parse NodeRED timestamp: 11/14/2025 2:48:28 PM"""
        try:
            return pd.to_datetime(time_str, format="%m/%d/%Y %I:%M:%S %p")
        except:
            return None
    
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add QC flags without removing data - transparency for adverse conditions"""
        # Initialize all as OK
        df['co2_qc'] = 'OK'
        df['temp_qc'] = 'OK'
        df['humidity_qc'] = 'OK'
        
        # Flag CO2 issues
        if self.config.co2_range:
            df.loc[df['co2'] < self.config.co2_range[0], 'co2_qc'] = 'BELOW_RANGE'
            df.loc[df['co2'] > self.config.co2_range[1], 'co2_qc'] = 'ABOVE_RANGE'
        
        # Flag temperature issues
        if self.config.temp_range:
            df.loc[df['temp'] < self.config.temp_range[0], 'temp_qc'] = 'BELOW_RANGE'
            df.loc[df['temp'] > self.config.temp_range[1], 'temp_qc'] = 'ABOVE_RANGE'
        
        # Flag humidity issues
        if self.config.humidity_range:
            df.loc[df['humidity'] < self.config.humidity_range[0], 'humidity_qc'] = 'BELOW_RANGE'
            df.loc[df['humidity'] > self.config.humidity_range[1], 'humidity_qc'] = 'ABOVE_RANGE'
        
        # Flag suspicious CO2 spikes (>500 ppm/min)
        if len(df) > 1:
            co2_diff = df['co2'].diff().abs()
            df.loc[co2_diff > 500, 'co2_qc'] = 'SPIKE'
        
        # Log QC summary
        qc_issues = (df['co2_qc'] != 'OK').sum()
        if qc_issues > 0:
            self.logger.info(
                f"QC flags: {qc_issues}/{len(df)} samples "
                f"({100*qc_issues/len(df):.1f}%)"
            )
        
        return df