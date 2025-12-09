"""Configuration management for sensor processing"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import yaml

# Determine the project root (src/ is inside repo root)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


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
    plots_dir: Path = Path("output/plots")  # NEW

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'PipelineConfig':
        """Load configuration from YAML file"""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        sensors = [SensorConfig(**s) for s in data['sensors']]

        return cls(
            sensors=sensors,
            excluded_sensor_ids=data.get('excluded_sensor_ids', []),
            output_dir=data.get('output_dir', 'output/individual'),
            parquet_dir=data.get('parquet_dir', 'output/parquet'),
            log_dir=data.get('log_dir', 'output/logs'),
            plots_dir=data.get('plots_dir', 'output/plots')
        )

    def resolve_path(self, p: Path) -> Path:
        """Resolve path relative to project root"""
        p = Path(p)
        return p if p.is_absolute() else PROJECT_ROOT / p

    def __post_init__(self):
        """Normalize and create all output directories"""
        # Resolve paths
        self.output_dir = self.resolve_path(self.output_dir)
        self.parquet_dir = self.resolve_path(self.parquet_dir)
        self.log_dir = self.resolve_path(self.log_dir)
        self.plots_dir = self.resolve_path(self.plots_dir)

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)

        # Resolve sensor input dirs
        for sensor in self.sensors:
            sensor.input_dir = self.resolve_path(sensor.input_dir)

    def get_sensor_output_paths(self, sensor_name: str):
        """Get output file paths for a sensor"""
        return {
            'csv': self.output_dir / f"{sensor_name}_10min.csv",
            'uptime': self.output_dir / f"{sensor_name}_uptime.csv"
        }
