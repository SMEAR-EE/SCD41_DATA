"""Main sensor data processing pipeline"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import json

from .config import PipelineConfig, SensorConfig
from .processor import DayProcessor


class SensorPipeline:
    """Orchestrates full sensor data processing pipeline"""
    
    def __init__(self, config: PipelineConfig, force: bool = False):
        """
        Initialise pipeline.
        
        Args:
            config: Pipeline configuration
            force: If True, reprocess all days (overwrite existing data)
        """
        self.config = config
        self.force = force
        self.logger = logging.getLogger(__name__)
    
    def run_sensor(
        self, 
        sensor_config: SensorConfig,
        year: Optional[int] = None,
        month: Optional[int] = None
    ):
        """
        Process single sensor.
        
        Args:
            sensor_config: Configuration for this sensor
            year: Process only this year (None = all)
            month: Process only this month (None = all)
        """
        self.logger.info("=" * 60)
        self.logger.info(f"Processing sensor: {sensor_config.name}")
        self.logger.info("=" * 60)
        
        # Get output paths (now per-sensor directories)
        paths = self.config.get_sensor_output_paths(sensor_config.name)
        
        # Initialise day processor
        day_processor = DayProcessor(sensor_config)
        
        # Group files by day
        daily_files = self._group_files_by_day(sensor_config, day_processor.parser)
        
        if not daily_files:
            self.logger.error(f"No files found in {sensor_config.input_dir}")
            return
        
        # Filter by date
        keys = sorted(daily_files.keys())
        if year:
            keys = [k for k in keys if k[0] == year]
        if month:
            keys = [k for k in keys if k[1] == month]
        if not keys:
            self.logger.warning(f"No files found for year={year}, month={month}")
            return
    
        self.logger.info(f"Found {len(keys)} days ({keys[0]} to {keys[-1]})")
    
        # Load already-processed days
        processed_days = set() if self.force else self._load_processed_days(paths['uptime'])
        
        if self.force and processed_days:
            self.logger.info(f"Force mode: reprocessing {len(processed_days)} days")
            self._clear_period_data(paths, year, month)
        
        # Process each day (handle force=True overwrite case)
        first_write = not paths['csv'].exists() or (self.force and year is None and month is None)
        processed_count = 0
        
        for day_key in keys:
            if not self.force and day_key in processed_days:
                self.logger.debug(f"Skipping {day_key} (already processed)")
                continue
            
            result = day_processor.process(daily_files[day_key], day_key)
            if result is None:
                continue
            
            df_10min, uptime_stats = result
            
            # Append to CSV (atomic write via temp file)
            self._safe_append_csv(df_10min, paths['csv'], first_write)
            
            # Log uptime
            self._log_uptime(uptime_stats, paths['uptime'])
            
            first_write = False
            processed_count += 1
        
        self.logger.info(f"Processed {processed_count} days")
        
        # Sort output if needed
        self._sort_output(paths['csv'])
        
        # Export monthly parquets to sensor's parquet directory
        self._export_parquets(
            sensor_config.name, 
            paths['csv'], 
            paths['parquet_dir'],
            year, 
            month
        )
        
        # Export monthly CSVs to sensor's csv directory
        self._export_monthly_csvs(
            sensor_config.name, 
            paths['csv'],
            paths['csv_dir'],
            year, 
            month
        )
        
        self._export_coverage_summary(sensor_config.name, paths)

        self.logger.info(f"✓ {sensor_config.name} complete\n")

    def run_all(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None
    ):
        """
        Process all sensors in configuration.
        
        Args:
            year: Process only this year (None = all)
            month: Process only this month (None = all)
        """
        self.logger.info("Starting pipeline for all sensors")
        
        for sensor_config in self.config.sensors:
            # Skip excluded sensors
            if sensor_config.sensor_id in self.config.excluded_sensor_ids:
                self.logger.info(
                    f"Skipping excluded sensor: {sensor_config.name} "
                    f"(ID: {sensor_config.sensor_id})"
                )
                continue
            
            try:
                self.run_sensor(sensor_config, year, month)
            except Exception as e:
                self.logger.error(
                    f"Failed to process {sensor_config.name}: {e}",
                    exc_info=True
                )
        
        self.logger.info("=" * 60)
        self.logger.info("Pipeline complete for all sensors")
        self.logger.info("=" * 60)

    def _group_files_by_day(
        self,
        sensor_config: SensorConfig,
        parser
    ) -> Dict[Tuple[int, int, int], List[Path]]:
        """Group sensor files by (year, month, day)"""
        pattern = parser.get_file_pattern()
        daily = {}
        
        for f in sensor_config.input_dir.glob(pattern):
            dt = parser.extract_datetime_from_filename(f.name)
            if dt is None:
                self.logger.debug(f"Skipping non-matching: {f.name}")
                continue
            
            key = (dt.year, dt.month, dt.day)
            daily.setdefault(key, []).append(f)
        
        # Sort files within each day
        for key in daily:
            daily[key] = sorted(daily[key])
        
        return daily

    def _load_processed_days(self, uptime_csv: Path) -> set:
        """Load set of already-processed (year, month, day) tuples"""
        if not uptime_csv.exists():
            return set()
        
        try:
            df = pd.read_csv(uptime_csv)
            return set(zip(df['year'], df['month'], df['day']))
        except Exception as e:
            self.logger.warning(f"Could not load uptime log: {e}")
            return set()

    def _safe_append_csv(self, df: pd.DataFrame, csv_path: Path, first_write: bool):
        """Append to CSV with atomic write (via temp file)"""
        # CRITICAL FIX: Reset index to make timestamp a column before writing
        # This prevents issues with index_label when timestamp is already in index
        df_to_write = df.reset_index()
        
        # Write to temp file first
        tmp_path = csv_path.parent / f".{csv_path.name}.tmp"
        
        if first_write:
            # New file - write directly
            df_to_write.to_csv(csv_path, index=False)
        else:
            # Append mode - write temp then atomic move
            df_to_write.to_csv(tmp_path, index=False, header=False)
            
            # Atomic append (concat files)
            with open(csv_path, 'ab') as f_out:
                with open(tmp_path, 'rb') as f_in:
                    f_out.write(f_in.read())
            
            # Remove temp file
            tmp_path.unlink()

    def _log_uptime(self, stats: Dict, uptime_csv: Path):
        """Append uptime stats to log CSV"""
        df = pd.DataFrame([stats])
        write_header = not uptime_csv.exists()
        df.to_csv(uptime_csv, mode='a', header=write_header, index=False)

    def _clear_period_data(
        self,
        paths: Dict[str, Path],
        year: Optional[int],
        month: Optional[int]
    ):
        """Clear data for specific period when force=True"""
        # Clear main CSV
        if paths['csv'].exists():
            df = pd.read_csv(paths['csv'], parse_dates=['timestamp'])
            mask = pd.Series(True, index=df.index)
            
            if year:
                mask &= df['timestamp'].dt.year == year
            if month:
                mask &= df['timestamp'].dt.month == month
            
            df = df[~mask]
            df.to_csv(paths['csv'], index=False)
            self.logger.info(f"Cleared period from {paths['csv'].name}")
        
        # Clear uptime CSV
        if paths['uptime'].exists():
            df = pd.read_csv(paths['uptime'])
            mask = pd.Series(True, index=df.index)
            
            if year:
                mask &= df['year'] == year
            if month:
                mask &= df['month'] == month
            
            df = df[~mask]
            df.to_csv(paths['uptime'], index=False)
            self.logger.info(f"Cleared period from {paths['uptime'].name}")

    def _sort_output(self, csv_path: Path):
        """Sort output CSV if timestamps are out of order"""
        if not csv_path.exists():
            return
        
        df = pd.read_csv(csv_path)
        
        # Robust timestamp parsing
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
        
        # Check for failed parsing
        if df['timestamp'].isna().all():
            self.logger.error(f"Failed to parse any timestamps in {csv_path}")
            return
        
        # Check if sorting is needed
        if len(df) > 1 and (df['timestamp'].diff().dropna() < pd.Timedelta(0)).any():
            self.logger.info("Sorting CSV by timestamp...")
            df = df.sort_values('timestamp')
            df.to_csv(csv_path, index=False)
    
    def _export_coverage_summary(self, sensor_name: str, paths: Dict):
        """Generate coverage summary JSON for a sensor."""
        
        uptime_path = paths['uptime']
        if not uptime_path.exists():
            return
        
        df = pd.read_csv(uptime_path)
        # pd.to_datetime(df[['year', 'month', 'day']])
        df['date'] = pd.to_datetime(
            df[['year', 'month', 'day']].rename(
                columns={'year': 'year', 'month': 'month', 'day': 'day'}
            )
        )
        df = df.sort_values('date')
        
        first = df['date'].min()
        last = df['date'].max()
        
        # Find missing days
        full_range = pd.date_range(first, last, freq='D')
        present = set(df['date'].dt.normalize())
        missing_days = sorted(set(full_range) - present)
        
        # Collapse consecutive missing days into ranges
        missing_ranges = []
        if missing_days:
            range_start = missing_days[0]
            prev = missing_days[0]
            for d in missing_days[1:]:
                if (d - prev).days > 1:
                    missing_ranges.append({
                        'start': range_start.strftime('%Y-%m-%d'),
                        'end': prev.strftime('%Y-%m-%d')
                    })
                    range_start = d
                prev = d
            missing_ranges.append({
                'start': range_start.strftime('%Y-%m-%d'),
                'end': prev.strftime('%Y-%m-%d')
            })
        
        # Expected 10-min records across operational window
        expected = len(pd.date_range(first, last, freq='10min'))
        actual = len(pd.read_csv(paths['csv']))
        
        summary = {
            'sensor': sensor_name,
            'first_observation': first.strftime('%Y-%m-%d'),
            'last_observation': last.strftime('%Y-%m-%d'),
            'expected_records_10min': expected,
            'actual_records': actual,
            'coverage_pct': round(100 * actual / expected, 1),
            'days_present': len(present),
            'days_missing': len(missing_days),
            'missing_ranges': missing_ranges
        }
        out_path = self.config.get_sensor_dirs(sensor_name)['base'] / f"{sensor_name}_coverage.json"

        with open(out_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(
            f"Coverage: {summary['coverage_pct']}% "
            f"({summary['days_missing']} days missing) → {out_path.name}"
        )

    def _export_parquets(
        self,
        sensor_name: str,
        csv_path: Path,
        parquet_dir: Path,
        year: Optional[int],
        month: Optional[int]
    ):
        """
        Export monthly parquet files.
        
        Output: {parquet_dir}/{sensor_name}_{year}_{month:02d}.parquet
        """
        if not csv_path.exists():
            return
        
        df = pd.read_csv(csv_path)
        
        # Robust timestamp parsing
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
        
        # Check for failed parsing
        if df['timestamp'].isna().all():
            self.logger.error(f"Failed to parse timestamps in {csv_path}, skipping parquet export")
            return
        
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        
        # Filter to requested period
        if year:
            df = df[df['year'] == year]
        if month:
            df = df[df['month'] == month]
        
        if df.empty:
            return
        
        # Export each month
        for (y, m), group in df.groupby(['year', 'month']):
            output_path = parquet_dir / f"{sensor_name}_{y}_{m:02d}.parquet"
            
            # Drop helper columns
            export_df = group.drop(columns=['year', 'month'])
            
            # Use pyarrow for compression
            table = pa.Table.from_pandas(export_df, preserve_index=False)
            pq.write_table(table, output_path, compression='snappy')
            
            self.logger.info(f"Exported {len(export_df)} rows → {output_path.name}")

    def _export_monthly_csvs(
        self,
        sensor_name: str,
        csv_path: Path,
        csv_dir: Path,
        year: Optional[int],
        month: Optional[int]
    ):
        """
        Export monthly CSV files.
        
        Output: {csv_dir}/{sensor_name}_{year}_{month:02d}.csv
        
        This gives consistent file organisation:
        - {sensor}_10min.csv          → Combined (working file)
        - {sensor}_{year}_{month}.csv → Monthly (publication-ready)
        - {sensor}_{year}_{month}.parquet → Monthly (efficient storage)
        """
        if not csv_path.exists():
            return
        
        df = pd.read_csv(csv_path)
        
        # Robust timestamp parsing
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
        
        # Check for failed parsing
        if df['timestamp'].isna().all():
            self.logger.error(f"Failed to parse timestamps in {csv_path}, skipping CSV export")
            return
        
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month
        
        # Filter to requested period
        if year:
            df = df[df['year'] == year]
        if month:
            df = df[df['month'] == month]
        
        if df.empty:
            return
        
        # Export each month
        for (y, m), group in df.groupby(['year', 'month']):
            output_path = csv_dir / f"{sensor_name}_{y}_{m:02d}.csv"
            
            # Drop helper columns
            export_df = group.drop(columns=['year', 'month'])
            
            # Write CSV
            export_df.to_csv(output_path, index=False)
            
            self.logger.info(f"Exported {len(export_df)} rows → {output_path.name}")