"""Configuration management for sensor processing"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import yaml


@dataclass
class SensorConfig:
    """Configuration for a single sensor"""
    name: str
    sensor_type: str  # 'scd41' or 'lgr_csv'
    sensor_id: Optional[str]
    input_dir: Path
    altitude_m: float
    expected_interval: int  # seconds
    
    # Validation ranges (None = no validation)
    co2_range: Optional[tuple] = None
    temp_range: Optional[tuple] = None
    humidity_range: Optional[tuple] = None
    
    def __post_init__(self):
        """Convert paths to Path objects"""
        self.input_dir = Path(self.input_dir)
        if self.co2_range:
            self.co2_range = tuple(self.co2_range)
        if self.temp_range:
            self.temp_range = tuple(self.temp_range)
        if self.humidity_range:
            self.humidity_range = tuple(self.humidity_range)


@dataclass
class PipelineConfig:
    """Configuration for entire processing pipeline"""
    sensors: List[SensorConfig]
    excluded_sensor_ids: List[str] = field(default_factory=list)
    output_dir: Path = Path("output/individual")
    parquet_dir: Path = Path("output/parquet")
    log_dir: Path = Path("output/logs")
    
    def __post_init__(self):
        """Convert paths and create directories"""
        self.output_dir = Path(self.output_dir)
        self.parquet_dir = Path(self.parquet_dir)
        self.log_dir = Path(self.log_dir)
        
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> 'PipelineConfig':
        """Load configuration from YAML file"""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        sensors = [SensorConfig(**s) for s in data['sensors']]
        
        return cls(
            sensors=sensors,
            excluded_sensor_ids=data.get('excluded_sensor_ids', []),
            output_dir=Path(data.get('output_dir', 'output/individual')),
            parquet_dir=Path(data.get('parquet_dir', 'output/parquet')),
            log_dir=Path(data.get('log_dir', 'output/logs'))
        )
    
    def get_sensor_output_paths(self, sensor_name: str):
        """Get output file paths for a sensor"""
        return {
            'csv': self.output_dir / f"{sensor_name}_10min.csv",
            'uptime': self.output_dir / f"{sensor_name}_uptime.csv"
        }