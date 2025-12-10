"""Multi-sensor data merger for aligned dataset"""
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


class SensorMerger:
    """
    Merge multiple sensor outputs into time-aligned dataset.
    
    Scientific Note on Data Alignment:
    ----------------------------------
    This merger performs an OUTER JOIN on timestamps, which means:
    
    1. ALL timestamps from ALL sensors are preserved
    2. Where a sensor has no data for a timestamp, values are NaN (missing)
    3. No interpolation or gap-filling is performed
    4. The merged dataset shows the TRUE data availability for each sensor
    
    Example:
        If LGR has data at 12:00 but SCD41 doesn't, the row will have:
        - timestamp: 2024-09-01 12:00:00
        - lgr_30m_co2_dry: 420.5
        - co2_30m_a_co2_mean: NaN (missing - sensor had no data)
    
    This preserves scientific rigor by making data gaps explicit rather than
    hiding them through interpolation.
    """
    
    def __init__(
        self, 
        output_dir: Path = Path("output/merged"),
        parquet_dir: Optional[Path] = None
    ):
        """
        Initialize merger
        
        Args:
            output_dir: Directory for merged CSV files
            parquet_dir: Directory for merged parquet files (default: output_dir/parquet)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.parquet_dir = Path(parquet_dir) if parquet_dir else self.output_dir / "parquet"
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def merge_sensors(
        self,
        sensor_csvs: dict,
        output_name: str = "SMEAR_EE_CO2_merged.csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        export_parquet: bool = True
    ) -> pd.DataFrame:
        """
        Merge multiple sensor CSVs into aligned dataset
        
        Args:
            sensor_csvs: Dict of {sensor_name: csv_path}
            output_name: Output filename for merged CSV
            start_date: Filter start (YYYY-MM-DD) or None
            end_date: Filter end (YYYY-MM-DD) or None
            export_parquet: If True, also export monthly parquet files
        
        Returns:
            Merged DataFrame with outer join on timestamps
        """
        self.logger.info(f"Merging {len(sensor_csvs)} sensors...")
        
        dfs = {}
        
        # Load each sensor
        for sensor_name, csv_path in sensor_csvs.items():
            self.logger.info(f"  Loading {sensor_name}...")
            
            # Parse timestamps with mixed format support to handle variations
            df = pd.read_csv(csv_path)
            
            if 'timestamp' not in df.columns:
                raise ValueError(f"{sensor_name}: CSV missing 'timestamp' column")
            
            # Robust timestamp parsing with format='mixed' to handle variations
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed', errors='coerce')
            
            # Drop rows with invalid timestamps
            invalid_ts = df['timestamp'].isna().sum()
            if invalid_ts > 0:
                self.logger.warning(f"    ⚠️  Found {invalid_ts} invalid timestamps in {sensor_name}, dropping them")
                df = df.dropna(subset=['timestamp'])
            
            df = df.set_index('timestamp')
            
            # Filter date range
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            # Check for duplicate timestamps
            dup_count = df.index.duplicated().sum()
            if dup_count > 0:
                self.logger.warning(f"    ⚠️  Found {dup_count} duplicate timestamps in {sensor_name}")
                self.logger.info(f"    Keeping last occurrence of duplicates")
                # Keep last occurrence (most recent data for that timestamp)
                df = df[~df.index.duplicated(keep='last')]
            
            # Rename columns with sensor prefix
            df.columns = [f"{sensor_name.lower()}_{col}" for col in df.columns]
            
            dfs[sensor_name] = df
            self.logger.info(f"    {len(df)} rows ({df.index.min()} to {df.index.max()})")
        
        # Merge on timestamp (OUTER JOIN - preserves all timestamps from all sensors)
        self.logger.info("  Merging on timestamp (OUTER JOIN - no data loss)...")
        merged = pd.concat(dfs.values(), axis=1, join='outer')
        
        # Sort by timestamp
        merged = merged.sort_index()
        
        # Add cross-sensor statistics for 30m cluster
        self.logger.info("  Computing cross-sensor statistics...")
        merged = self._add_cross_sensor_stats(merged)
        
        # Log merge quality
        self._log_merge_quality(merged, dfs)
        
        # Save CSV
        output_path = self.output_dir / output_name
        merged.reset_index().to_csv(output_path, index=False)
        self.logger.info(f"✓ Saved merged dataset: {output_path}")
        self.logger.info(f"  Shape: {merged.shape[0]} rows × {merged.shape[1]} columns")
        
        # Export monthly parquets if requested
        if export_parquet:
            self._export_monthly_parquet(merged)
        
        return merged
    
    def _add_cross_sensor_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add statistics for co-located sensors (30m cluster)
        
        Computes mean and std across 3 SCD41 sensors at 30m.
        
        Scientific Note:
        ----------------
        These cluster statistics are computed ONLY from available data.
        If only 1 sensor has data at a timestamp:
          - mean = that sensor's value
          - std = NaN (cannot compute std from 1 point)
          - count = 1
        
        This makes missing data explicit in the statistics.
        """
        # Find 30m CO2 columns
        co2_30m_cols = [c for c in df.columns if 'co2_30m_' in c and c.endswith('_co2_mean')]
        
        if len(co2_30m_cols) >= 2:
            self.logger.info(f"    Computing stats for {len(co2_30m_cols)} co-located sensors")
            
            # Mean across available sensors (NaN if all missing)
            df['scd41_30m_cluster_co2_mean'] = df[co2_30m_cols].mean(axis=1)
            
            # Std across available sensors (NaN if <2 sensors have data)
            df['scd41_30m_cluster_co2_std'] = df[co2_30m_cols].std(axis=1)
            
            # Count of valid measurements at each timestamp
            df['scd41_30m_cluster_co2_count'] = df[co2_30m_cols].notna().sum(axis=1)
        
        return df
    
    def _log_merge_quality(self, merged: pd.DataFrame, original_dfs: dict):
        """
        Log data coverage statistics
        
        Coverage = (timestamps with data) / (total timestamps)
        """
        self.logger.info("  Merge Quality Report:")
        
        total_timestamps = len(merged)
        
        for sensor_name, df in original_dfs.items():
            # Count how many timestamps have data for this sensor
            sensor_cols = [c for c in merged.columns if c.startswith(sensor_name.lower())]
            
            if sensor_cols:
                # Check first column as proxy for sensor presence
                coverage = merged[sensor_cols[0]].notna().sum()
                coverage_pct = 100 * coverage / total_timestamps
                
                self.logger.info(
                    f"    {sensor_name}: {coverage}/{total_timestamps} "
                    f"({coverage_pct:.1f}% coverage)"
                )
        
        # Check for gaps (timestamps with NO sensor data)
        all_data_cols = [c for c in merged.columns if not c.endswith('_qc')]
        completely_empty = merged[all_data_cols].isna().all(axis=1).sum()
        
        if completely_empty > 0:
            self.logger.warning(
                f"    ⚠️ {completely_empty} timestamps have NO data from any sensor"
            )
    
    def export_monthly_csv(
        self,
        merged_df: pd.DataFrame,
        base_name: str = "SMEAR_EE_CO2"
    ):
        """
        Export monthly subsets of merged data as CSV
        
        Args:
            merged_df: Full merged DataFrame
            base_name: Base name for output files
        """
        self.logger.info("Exporting monthly merged CSV files...")
        
        # Ensure timestamp is index
        if 'timestamp' in merged_df.columns:
            merged_df = merged_df.set_index('timestamp')
        
        # Group by year-month
        merged_df['year'] = merged_df.index.year
        merged_df['month'] = merged_df.index.month
        
        for (year, month), group in merged_df.groupby(['year', 'month']):
            # Drop helper columns
            export_df = group.drop(columns=['year', 'month'])
            
            # Save as CSV
            filename = f"{base_name}_{year}_{month:02d}_merged.csv"
            export_df.reset_index().to_csv(self.output_dir / filename, index=False)
            
            self.logger.info(f"  Saved: {filename} ({len(export_df)} rows)")
    
    def _export_monthly_parquet(
        self,
        merged_df: pd.DataFrame,
        base_name: str = "SMEAR_EE_CO2"
    ):
        """
        Export monthly subsets of merged data as Parquet files
        
        Parquet advantages:
        - ~10x smaller file size (snappy compression)
        - Faster to read in Python/R
        - Preserves data types exactly
        - Column-oriented storage for efficient queries
        
        Args:
            merged_df: Full merged DataFrame (with timestamp as index)
            base_name: Base name for output files
        """
        self.logger.info("Exporting monthly merged Parquet files...")
        
        # Ensure timestamp is in the dataframe (reset index if needed)
        if 'timestamp' not in merged_df.columns:
            merged_df = merged_df.reset_index()
        
        # Add year/month for grouping
        merged_df['year'] = pd.to_datetime(merged_df['timestamp']).dt.year
        merged_df['month'] = pd.to_datetime(merged_df['timestamp']).dt.month
        
        # Export each month
        for (year, month), group in merged_df.groupby(['year', 'month']):
            # Drop helper columns
            export_df = group.drop(columns=['year', 'month'])
            
            # Save as Parquet
            filename = f"{base_name}_{year}_{month:02d}_merged.parquet"
            output_path = self.parquet_dir / filename
            
            # Use pyarrow for compression
            table = pa.Table.from_pandas(export_df, preserve_index=False)
            pq.write_table(table, output_path, compression='snappy')
            
            self.logger.info(f"  Saved: {filename} ({len(export_df)} rows)")


# Convenience function
def merge_all_sensors(
    individual_dir: Path,
    sensor_names: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    output_dir: Optional[Path] = None,
    parquet_dir: Optional[Path] = None,
    export_parquet: bool = True
) -> pd.DataFrame:
    """
    Merge all sensors from individual/ directory
    
    Args:
        individual_dir: Path to output/individual/
        sensor_names: List of sensor names to merge
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        output_dir: Output directory for merged files (default: individual_dir/../merged)
        parquet_dir: Output directory for parquet files (default: output_dir/parquet)
        export_parquet: If True, also export monthly parquet files
    
    Returns:
        Merged DataFrame
    
    Example:
        merged = merge_all_sensors(
            Path("output/individual"),
            ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"],
            output_dir=Path("output/merged")
        )
    """
    # Default output_dir to sibling of individual_dir
    if output_dir is None:
        output_dir = individual_dir.parent / "merged"
    
    merger = SensorMerger(output_dir=output_dir, parquet_dir=parquet_dir)
    
    # Build dict of sensor CSVs
    sensor_csvs = {}
    for name in sensor_names:
        csv_path = individual_dir / f"{name}_10min.csv"
        if csv_path.exists():
            sensor_csvs[name] = csv_path
        else:
            logging.warning(f"CSV not found: {csv_path}")
    
    # Merge
    merged = merger.merge_sensors(
        sensor_csvs, 
        start_date=start_date, 
        end_date=end_date,
        export_parquet=export_parquet
    )
    
    # Also export monthly CSV
    merger.export_monthly_csv(merged)
    
    return merged