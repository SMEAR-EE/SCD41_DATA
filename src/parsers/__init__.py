"""Sensor data parsers for different file formats.

This module provides parser implementations for various sensor data formats:

- BaseSensorParser: Abstract base class defining the parser interface
- SCD41Parser: Parses NodeRED JSON format from SCD41 sensors (handles nested dicts)
- LGRParser: Parses LGR CSV format (27-column structure with multiple gases)

Each parser:
- Extracts timestamps from filenames for day grouping
- Parses raw sensor data into standardized DataFrames
- Adds quality control (QC) flags without removing data
- Returns DataFrames with consistent column naming

Example usage:
    from parsers import SCD41Parser
    
    parser = SCD41Parser(config, sensor_id='A')
    df = parser.parse_file(Path('SCD41_A.json-2024-09-01'))
    # Returns DataFrame with columns: [timestamp, co2, temp, humidity, co2_qc, ...]
"""
from .base_parser import BaseSensorParser
from .scd41_parser import SCD41Parser
from .lgr_parser import LGRParser

__all__ = ['BaseSensorParser', 'SCD41Parser', 'LGRParser']