"""Configuration management for sensor processing

Directory Structure (after refactor):
-------------------------------------
output/
├── sensors/                    # Per-sensor outputs
│   ├── CO2_SCT1_2M/
│   │   ├── csv/               # 10min.csv, monthly CSVs, uptime
│   │   ├── parquet/           # Monthly parquet files
│   │   └── plots/             # Sensor-specific visualisations
│   ├── CO2_30M_A/
│   │   └── ...
│   └── LGR_30M/
│       └── ...
├── merged/                     # Cross-sensor merged data
│   ├── csv/                   # Merged CSV files
│   └── parquet/               # Merged parquet files
└── logs/                       # Processing logs
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict
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

    # Base directories (new structure)
    sensors_dir: Path = Path("output/sensors")   # Per-sensor outputs
    merged_dir: Path = Path("output/merged")     # Merged outputs
    log_dir: Path = Path("output/logs")          # Processing logs

    # Legacy compatibility properties (deprecated - use get_sensor_output_paths)
    @property
    def output_dir(self) -> Path:
        """Deprecated: use get_sensor_output_paths() instead"""
        return self.sensors_dir
    
    @property
    def parquet_dir(self) -> Path:
        """Deprecated: use get_sensor_output_paths() instead"""
        return self.sensors_dir
    
    @property
    def plots_dir(self) -> Path:
        """Deprecated: use get_sensor_output_paths() instead"""
        return self.sensors_dir

    @classmethod
    def from_yaml(cls, config_path: Path) -> 'PipelineConfig':
        """Load configuration from YAML file"""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        
        sensors = [SensorConfig(**s) for s in data['sensors']]

        return cls(
            sensors=sensors,
            excluded_sensor_ids=data.get('excluded_sensor_ids', []),
            sensors_dir=Path(data.get('sensors_dir', data.get('output_dir', 'output/sensors'))),
            merged_dir=Path(data.get('merged_dir', 'output/merged')),
            log_dir=Path(data.get('log_dir', 'output/logs'))
        )

    def resolve_path(self, p: Path) -> Path:
        """Resolve path relative to project root"""
        p = Path(p)
        return p if p.is_absolute() else PROJECT_ROOT / p

    def __post_init__(self):
        """Normalise and create all output directories"""
        # Resolve base paths
        self.sensors_dir = self.resolve_path(self.sensors_dir)
        self.merged_dir = self.resolve_path(self.merged_dir)
        self.log_dir = self.resolve_path(self.log_dir)

        # Create base directories
        self.sensors_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create merged subdirectories
        (self.merged_dir / "csv").mkdir(parents=True, exist_ok=True)
        (self.merged_dir / "parquet").mkdir(parents=True, exist_ok=True)

        # Create per-sensor directories
        for sensor in self.sensors:
            sensor.input_dir = self.resolve_path(sensor.input_dir)
            dirs = self.get_sensor_dirs(sensor.name)
            for d in dirs.values():
                d.mkdir(parents=True, exist_ok=True)

    def get_sensor_dirs(self, sensor_name: str) -> Dict[str, Path]:
        """
        Get directory paths for a sensor.
        
        Returns:
            Dict with keys: 'base', 'csv', 'parquet', 'plots'
        """
        base = self.sensors_dir / sensor_name
        return {
            'base': base,
            'csv': base / 'csv',
            'parquet': base / 'parquet',
            'plots': base / 'plots'
        }

    def get_sensor_output_paths(self, sensor_name: str) -> Dict[str, Path]:
        """
        Get output file paths for a sensor.
        
        Returns:
            Dict with keys:
                'csv'         - Main 10min CSV file
                'uptime'      - Uptime log CSV
                'csv_dir'     - Directory for monthly CSVs
                'parquet_dir' - Directory for parquet files
                'plots_dir'   - Directory for plots
        """
        dirs = self.get_sensor_dirs(sensor_name)
        return {
            'csv': dirs['csv'] / f"{sensor_name}_10min.csv",
            'uptime': dirs['csv'] / f"{sensor_name}_uptime.csv",
            'csv_dir': dirs['csv'],
            'parquet_dir': dirs['parquet'],
            'plots_dir': dirs['plots']
        }

    def get_merged_dirs(self) -> Dict[str, Path]:
        """
        Get directory paths for merged outputs.
        
        Returns:
            Dict with keys: 'base', 'csv', 'parquet'
        """
        return {
            'base': self.merged_dir,
            'csv': self.merged_dir / 'csv',
            'parquet': self.merged_dir / 'parquet'
        }

    def get_all_sensor_names(self) -> List[str]:
        """Get list of all sensor names from config"""
        return [s.name for s in self.sensors]

    def iter_sensor_csvs(self) -> Dict[str, Path]:
        """
        Iterate over all sensor 10min CSV paths.
        
        Useful for merger to find input files.
        
        Returns:
            Dict of {sensor_name: csv_path}
        """
        return {
            s.name: self.get_sensor_output_paths(s.name)['csv']
            for s in self.sensors
            if s.sensor_id not in self.excluded_sensor_ids
        }

    def iter_sensor_parquet_dirs(self) -> Dict[str, Path]:
        """
        Iterate over all sensor parquet directories.
        
        Returns:
            Dict of {sensor_name: parquet_dir}
        """
        return {
            s.name: self.get_sensor_output_paths(s.name)['parquet_dir']
            for s in self.sensors
            if s.sensor_id not in self.excluded_sensor_ids
        }