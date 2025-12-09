"""Parser for LGR (Los Gatos Research) sensor data files"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging
import re

from .base_parser import BaseSensorParser

logger = logging.getLogger(__name__)


class LGRParser(BaseSensorParser):
    """Parser for LGR (Los Gatos Research) sensor data files."""
    
    # Define the column names based on the LGR file format
    COLUMN_NAMES = [
        'timestamp_raw',      # Column 0: YYYYMMDDHHMMSS format
        'sequence',           # Column 1: Sequence number
        'quality',            # Column 2: Quality indicator
        'datetime_formatted', # Column 3: MM/DD/YYYYHH:MM:SS.mmm format
        'CH4_ppm',           # Column 4: Methane in ppm
        'CH4_ppm_sd',        # Column 5: CH4 standard deviation
        'H2O_ppm',           # Column 6: Water vapor in ppm
        'H2O_ppm_sd',        # Column 7: H2O standard deviation
        'CO2_ppm',           # Column 8: Carbon dioxide in ppm
        'CO2_ppm_sd',        # Column 9: CO2 standard deviation
        'CH4_dry',           # Column 10: Dry CH4
        'CH4_dry_sd',        # Column 11: Dry CH4 standard deviation
        'CO2_dry',           # Column 12: Dry CO2
        'CO2_dry_sd',        # Column 13: Dry CO2 standard deviation
        'GasP_torr',         # Column 14: Gas pressure in torr
        'GasP_torr_sd',      # Column 15: Gas pressure standard deviation
        'GasT_C',            # Column 16: Gas temperature in Celsius
        'GasT_C_sd',         # Column 17: Gas temperature standard deviation
        'AmbT_C',            # Column 18: Ambient temperature in Celsius
        'AmbT_C_sd',         # Column 19: Ambient temperature standard deviation
        'RD0_us',            # Column 20: Ring-down time 0
        'RD0_us_sd',         # Column 21: Ring-down time 0 standard deviation
        'RD1_us',            # Column 22: Ring-down time 1
        'RD1_us_sd',         # Column 23: Ring-down time 1 standard deviation
        'Fit_Flag',          # Column 24: Fit flag
        'MIU_VALVE',         # Column 25: MIU valve status
        'MIU_Description'    # Column 26: MIU description
    ]
    
    def __init__(self, config):
        """
        Initialize the LGR parser.
        
        Args:
            config: SensorConfig object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized LGR parser for sensor: {config.name}")
    
    def get_file_pattern(self) -> str:
        """Return glob pattern for LGR files"""
        return "*.co2ch4"
    
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract datetime from LGR filename: 20240901000000.co2ch4
        Format: YYYYMMDDHHMMSS.co2ch4
        """
        pattern = re.compile(r"(\d{14})\.co2ch4")
        m = pattern.match(filename)
        if not m:
            return None
        
        timestamp_str = m.group(1)
        try:
            return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        except ValueError:
            return None
    
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse a single LGR data file.
        
        Args:
            file_path: Path to the LGR CSV file
            
        Returns:
            DataFrame with parsed data, or None if parsing fails
        """
        try:
            self.logger.info(f"Parsing LGR file: {file_path}")
            
            # Read CSV without header, using defined column names
            df = pd.read_csv(
                file_path,
                header=None,  # CRITICAL: No header row in the file
                names=self.COLUMN_NAMES,
                na_values=['', 'NA', 'NaN'],
                keep_default_na=True
            )
            
            # Parse timestamp from the raw timestamp column (YYYYMMDDHHMMSS format)
            df['timestamp'] = pd.to_datetime(
                df['timestamp_raw'].astype(str),
                format='%Y%m%d%H%M%S',
                errors='coerce'
            )
            
            # Check for parsing errors
            invalid_times = df['timestamp'].isna().sum()
            if invalid_times > 0:
                self.logger.warning(
                    f"Found {invalid_times} rows with invalid timestamps in {file_path.name}"
                )
            
            # Drop rows with invalid timestamps
            df = df.dropna(subset=['timestamp'])
            
            if len(df) == 0:
                self.logger.warning(f"No valid data in {file_path.name}")
                return None
            
            # Sort by time to ensure chronological order
            df = df.sort_values('timestamp')
            
            # Add QC flags
            df = self.add_qc_flags(df)
            
            # Drop metadata columns that shouldn't be resampled
            # Keep only measurement data and QC flags
            metadata_cols = [
                'timestamp_raw',      # Parsing helper
                'datetime_formatted', # Parsing helper
                'sequence',          # Not a measurement
                'MIU_VALVE',         # Metadata
                'MIU_Description'    # Metadata
            ]
            cols_to_drop = [col for col in metadata_cols if col in df.columns]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
                self.logger.debug(f"Dropped metadata columns: {cols_to_drop}")
            
            # Log some basic statistics
            self.logger.info(f"Parsed {len(df)} valid records from {file_path.name}")
            self.logger.info(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to parse {file_path}: {e}")
            return None
    
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add quality control flags for LGR data without removing data.
        
        Flags based on:
        - Quality indicator (column 2)
        - Fit flag (column 24)
        - CO2 dry mole fraction ranges
        - Pressure and temperature ranges
        """
        # Initialize all as OK
        df['co2_qc'] = 'OK'
        df['quality_qc'] = 'OK'
        
        # Flag based on quality indicator (should be close to 100)
        if 'quality' in df.columns:
            df.loc[df['quality'] < 95, 'quality_qc'] = 'LOW_QUALITY'
        
        # Flag based on fit flag (3 is good, other values indicate issues)
        if 'Fit_Flag' in df.columns:
            df.loc[df['Fit_Flag'] != 3, 'quality_qc'] = 'BAD_FIT'
        
        # Flag CO2 issues based on dry mole fraction
        if self.config.co2_range and 'CO2_dry' in df.columns:
            df.loc[df['CO2_dry'] < self.config.co2_range[0], 'co2_qc'] = 'BELOW_RANGE'
            df.loc[df['CO2_dry'] > self.config.co2_range[1], 'co2_qc'] = 'ABOVE_RANGE'
        
        # Flag extreme values that might indicate sensor issues
        if 'CO2_dry' in df.columns:
            # Flag unrealistic values (< 300 or > 1000 ppm is very unusual for ambient air)
            df.loc[df['CO2_dry'] < 300, 'co2_qc'] = 'UNREALISTIC_LOW'
            df.loc[df['CO2_dry'] > 1000, 'co2_qc'] = 'UNREALISTIC_HIGH'
        
        # Flag temperature issues (instrument operating range)
        if 'GasT_C' in df.columns:
            df.loc[df['GasT_C'] < -40, 'quality_qc'] = 'TEMP_TOO_LOW'
            df.loc[df['GasT_C'] > 50, 'quality_qc'] = 'TEMP_TOO_HIGH'
        
        # Log QC summary
        qc_issues = (df['co2_qc'] != 'OK').sum() + (df['quality_qc'] != 'OK').sum()
        if qc_issues > 0:
            self.logger.info(
                f"QC flags: {qc_issues} issues in {len(df)} samples "
                f"({100*qc_issues/len(df):.1f}%)"
            )
        
        return df
    
    def get_co2_columns(self) -> dict:
        """
        Get the mapping of CO2-related columns.
        
        Returns:
            Dictionary with column names for CO2 data
        """
        return {
            'co2': 'CO2_dry',           # Main CO2 column (dry mole fraction)
            'co2_wet': 'CO2_ppm',       # Wet CO2 concentration
            'co2_uncertainty': 'CO2_dry_sd',  # Uncertainty in dry CO2
            'temp': 'GasT_C',           # Gas temperature
            'pressure': 'GasP_torr'     # Gas pressure
        }


# For testing only
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    class MockConfig:
        name = "LGR_TEST"
        co2_range = [350, 600]
    
    parser = LGRParser(MockConfig())
    print("LGR Parser initialized successfully")