"""Abstract base class for sensor parsers"""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd


class BaseSensorParser(ABC):
    """Abstract base for all sensor parsers"""
    
    @abstractmethod
    def parse_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Parse single file and return standardized DataFrame
        
        Returns:
            DataFrame with columns: [timestamp, co2, temp, humidity, ...]
            Must have 'timestamp' column
        """
        pass
    
    @abstractmethod
    def get_file_pattern(self) -> str:
        """Return glob pattern for this sensor's files"""
        pass
    
    @abstractmethod
    def extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """Parse timestamp from filename for day grouping"""
        pass
    
    @abstractmethod
    def add_qc_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add quality control flags without removing data"""
        pass