"""
LGR sensor data parser - Fixed version for headerless CSV files
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LGRParser:
    """Parser for LGR (Los Gatos Research) sensor data files."""
    
    # Define the column names based on the LGR file format
    # Adjust these based on your actual LGR sensor configuration
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
    
    def __init__(self):
        """Initialize the LGR parser."""
        pass
    
    def parse_file(self, file_path: Path) -> pd.DataFrame:
        """
        Parse a single LGR data file.
        
        Args:
            file_path: Path to the LGR CSV file
            
        Returns:
            DataFrame with parsed data
            
        Raises:
            Exception: If file parsing fails
        """
        try:
            logger.info(f"Parsing LGR file: {file_path}")
            
            # Read CSV without header, using defined column names
            df = pd.read_csv(
                file_path,
                header=None,  # No header row in the file
                names=self.COLUMN_NAMES,
                na_values=['', 'NA', 'NaN'],
                keep_default_na=True
            )
            
            # Parse timestamp from the raw timestamp column (YYYYMMDDHHMMSS format)
            df['Time'] = pd.to_datetime(
                df['timestamp_raw'].astype(str),
                format='%Y%m%d%H%M%S',
                errors='coerce'
            )
            
            # Alternative: Could also parse from the formatted datetime column if preferred
            # df['Time'] = pd.to_datetime(
            #     df['datetime_formatted'],
            #     format='%m/%d/%Y%H:%M:%S.%f',
            #     errors='coerce'
            # )
            
            # Check for parsing errors
            invalid_times = df['Time'].isna().sum()
            if invalid_times > 0:
                logger.warning(f"Found {invalid_times} rows with invalid timestamps in {file_path.name}")
            
            # Drop rows with invalid timestamps
            df = df.dropna(subset=['Time'])
            
            # Set Time as index
            df.set_index('Time', inplace=True)
            
            # Sort by time to ensure chronological order
            df.sort_index(inplace=True)
            
            # Log some basic statistics
            logger.info(f"Parsed {len(df)} valid records from {file_path.name}")
            logger.info(f"Time range: {df.index.min()} to {df.index.max()}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            raise
    
    def get_co2_columns(self) -> dict:
        """
        Get the mapping of CO2-related columns.
        
        Returns:
            Dictionary with column names for CO2 data
        """
        return {
            'co2_wet': 'CO2_ppm',      # Wet CO2 concentration
            'co2_dry': 'CO2_dry',       # Dry CO2 concentration (typically what you want)
            'co2_uncertainty': 'CO2_dry_sd'  # Uncertainty in dry CO2
        }
    
    def parse_directory(self, directory: Path, file_pattern: str = "*.co2ch4") -> pd.DataFrame:
        """
        Parse all LGR files in a directory.
        
        Args:
            directory: Path to directory containing LGR files
            file_pattern: Glob pattern for file matching
            
        Returns:
            Combined DataFrame from all files
        """
        all_data = []
        
        file_list = sorted(directory.glob(file_pattern))
        logger.info(f"Found {len(file_list)} LGR files to parse")
        
        for file_path in file_list:
            try:
                df = self.parse_file(file_path)
                all_data.append(df)
            except Exception as e:
                logger.error(f"Skipping file {file_path.name} due to error: {e}")
                continue
        
        if not all_data:
            logger.warning("No data was successfully parsed")
            return pd.DataFrame()
        
        # Concatenate all dataframes
        combined_df = pd.concat(all_data, axis=0)
        
        # Remove any duplicate timestamps (keep first occurrence)
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
        
        # Sort by time
        combined_df.sort_index(inplace=True)
        
        logger.info(f"Combined dataset: {len(combined_df)} total records")
        logger.info(f"Time range: {combined_df.index.min()} to {combined_df.index.max()}")
        
        return combined_df


# Example usage for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with a sample file
    parser = LGRParser()
    
    # Example: Parse a single file
    # df = parser.parse_file(Path("/path/to/20240901000000.co2ch4"))
    # print(df.head())
    # print("\nCO2 columns:", parser.get_co2_columns())