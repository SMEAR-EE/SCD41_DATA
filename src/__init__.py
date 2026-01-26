"""Sensor data processing pipeline

Per-sensor directory structure:
    output/sensors/{sensor}/csv/     - CSV files
    output/sensors/{sensor}/parquet/ - Parquet files  
    output/sensors/{sensor}/plots/   - Visualisations
    output/merged/csv/               - Merged CSVs
    output/merged/parquet/           - Merged parquets
"""
from .config import SensorConfig, PipelineConfig
from .pipeline import SensorPipeline
from .merger import SensorMerger, merge_all_sensors

__all__ = [
    'SensorConfig', 
    'PipelineConfig', 
    'SensorPipeline',
    'SensorMerger',
    'merge_all_sensors'
]