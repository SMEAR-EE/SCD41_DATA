"""Parser for LGR CSV files"""
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from .base_parser import BaseSensorParser


class LGRParser(BaseSensorParser):
    """Parser for LGR structured CSV logs"""
    
    # LGR column mapping (all scientific columns)
    COLUMN_MAP = {
        'Time': 'timestamp',
        '[CH4]_ppm': 'ch4',
        '[CH4]_ppm_sd': 'ch4_sd',
        '[H2O]_ppm': 'h2o',
        '[H2O]_ppm_sd': 'h2o_sd',
        '[CO2]_ppm': 'co2',
        '[CO2]_ppm_sd': 'co2_sd',
        '[CH4]d_ppm': 'ch4_dry',
        '[CH4]d_ppm_sd': 'ch4_dry_sd',
        '[CO2]d_ppm': 'co2_dry',        # Water-corrected CO2 (critical!)
        '[CO2]d_ppm_sd': 'co2_dry_sd',
        'GasP_torr': 'gas_pressure',
        'GasT_C': 'gas_temp',
        'AmbT_C': 'ambient_temp'
    }
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def get_file_pattern(self) -> str:
        """Match files like: 20251114143000.co2ch4"""
        return "*.co2ch4"
    
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse LGR CSV with 2-line header:
        Line 1: VC:2f90039 BD:Jan 16 2014 SN:LGR-15-0203
        Line 2: Time, [CH4]_ppm, ...
        """
        try:
            # Skip metadata lines (first 2 lines)
            df = pd.read_csv(file_path, skiprows=2, skipinitialspace=True)
            
            # Parse timestamp
            df['timestamp'] = pd.to_datetime(
                df['Time'], 
                format='%m/%d/%Y %H:%M:%S.%f',
                errors='coerce'
            )
            
            # Drop rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
            
            # Rename columns to standardized names
            cols_to_keep = {}
            for lgr_col, std_col in self.COLUMN_MAP.items():
                if lgr_col in df.columns:
                    cols_to_keep[lgr_col] = std_col
            
            df = df.rename(columns=cols_to_keep)
            
            # Select only mapped columns
            available_cols = ['timestamp'] + [c for c in cols_to_keep.values() if c in df.columns]
            df = df[available_cols]
            
            # Log if any expected columns missing
            missing = set(self.COLUMN_MAP.values()) - set(df.columns)
            if missing:
                self.logger.warning(
                    f"{file_path.name}: Missing columns: {missing}"
                )
            
            return self.add_qc_flags(df)
        
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract from: 20251114143000.co2ch4
        Format: YYYYMMDDHHMMSS
        """
        pattern = re.compile(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})\.co2ch4")
        m = pattern.match(filename)
        if not m:
            return None
        
        Y, M, D, h, m_val, s = m.groups()
        return datetime(int(Y), int(M), int(D), int(h), int(m_val), int(s))
    
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add QC flags for LGR data"""
        df['co2_qc'] = 'OK'
        df['co2_dry_qc'] = 'OK'
        
        # LGR has wider valid range (0-20000 ppm)
        if self.config.co2_range:
            if 'co2' in df.columns:
                df.loc[df['co2'] < self.config.co2_range[0], 'co2_qc'] = 'BELOW_RANGE'
                df.loc[df['co2'] > self.config.co2_range[1], 'co2_qc'] = 'ABOVE_RANGE'
            
            if 'co2_dry' in df.columns:
                df.loc[df['co2_dry'] < self.config.co2_range[0], 'co2_dry_qc'] = 'BELOW_RANGE'
                df.loc[df['co2_dry'] > self.config.co2_range[1], 'co2_dry_qc'] = 'ABOVE_RANGE'
        
        # Log QC summary
        qc_issues = ((df['co2_qc'] != 'OK') | (df['co2_dry_qc'] != 'OK')).sum()
        if qc_issues > 0:
            self.logger.info(
                f"QC flags: {qc_issues}/{len(df)} samples"
            )
        
        return df