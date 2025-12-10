"""Multi-sensor data merger for aligned dataset"""
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np


class SensorMerger:
    """Merge multiple sensor outputs into time-aligned dataset"""
    
    def __init__(self, output_dir: Path = Path("output/merged")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def merge_sensors(
        self,
        sensor_csvs: dict,
        output_name: str = "SMEAR_EE_CO2_merged.csv",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Merge multiple sensor CSVs into aligned dataset
        
        Args:
            sensor_csvs: Dict of {sensor_name: csv_path}
            output_name: Output filename
            start_date: Filter start (YYYY-MM-DD) or None
            end_date: Filter end (YYYY-MM-DD) or None
        
        Returns:
            Merged DataFrame
        """
        self.logger.info(f"Merging {len(sensor_csvs)} sensors...")
        
        dfs = {}
        
        # Load each sensor
        for sensor_name, csv_path in sensor_csvs.items():
            self.logger.info(f"  Loading {sensor_name}...")
            
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            df = df.set_index('timestamp')
            
            # Filter date range
            if start_date:
                df = df[df.index >= start_date]
            if end_date:
                df = df[df.index <= end_date]
            
            # DEBUG: Check for duplicate timestamps
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
        
        # Merge on timestamp (outer join keeps all timestamps)
        self.logger.info("  Merging on timestamp...")
        merged = pd.concat(dfs.values(), axis=1, join='outer')
        
        # Sort by timestamp
        merged = merged.sort_index()
        
        # Add cross-sensor statistics for 30m cluster
        self.logger.info("  Computing cross-sensor statistics...")
        merged = self._add_cross_sensor_stats(merged)
        
        # Log merge quality
        self._log_merge_quality(merged, dfs)
        
        # Save
        output_path = self.output_dir / output_name
        merged.reset_index().to_csv(output_path, index=False)
        self.logger.info(f"✓ Saved merged dataset: {output_path}")
        self.logger.info(f"  Shape: {merged.shape[0]} rows × {merged.shape[1]} columns")
        
        return merged
    
    def _add_cross_sensor_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add statistics for co-located sensors (30m cluster)
        
        Computes mean and std across 3 SCD41 sensors at 30m
        """
        # Find 30m CO2 columns
        co2_30m_cols = [c for c in df.columns if 'co2_30m_' in c and c.endswith('_co2_mean')]
        
        if len(co2_30m_cols) >= 2:
            self.logger.info(f"    Computing stats for {len(co2_30m_cols)} co-located sensors")
            
            # Mean across 3 sensors
            df['scd41_30m_cluster_co2_mean'] = df[co2_30m_cols].mean(axis=1)
            
            # Std across 3 sensors (inter-sensor variability)
            df['scd41_30m_cluster_co2_std'] = df[co2_30m_cols].std(axis=1)
            
            # Count of valid measurements
            df['scd41_30m_cluster_co2_count'] = df[co2_30m_cols].notna().sum(axis=1)
        
        return df
    
    def _log_merge_quality(self, merged: pd.DataFrame, original_dfs: dict):
        """Log data coverage statistics"""
        self.logger.info("  Merge Quality Report:")
        
        total_timestamps = len(merged)
        
        for sensor_name, df in original_dfs.items():
            # Count how many timestamps have data for this sensor
            sensor_cols = [c for c in merged.columns if c.startswith(sensor_name.lower())]
            
            if sensor_cols:
                # Check first column as proxy
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
    
    def export_monthly_merged(
        self,
        merged_df: pd.DataFrame,
        base_name: str = "SMEAR_EE_CO2"
    ):
        """
        Export monthly subsets of merged data
        
        Args:
            merged_df: Full merged DataFrame
            base_name: Base name for output files
        """
        self.logger.info("Exporting monthly merged files...")
        
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


# Convenience function
def merge_all_sensors(
    individual_dir: Path,
    sensor_names: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Merge all sensors from individual/ directory
    
    Args:
        individual_dir: Path to output/individual/
        sensor_names: List of sensor names to merge
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    
    Returns:
        Merged DataFrame
    
    Example:
        merged = merge_all_sensors(
            Path("output/individual"),
            ["CO2_SCT1_2M", "CO2_30M_A", "CO2_30M_B", "CO2_30M_C", "LGR_30M"]
        )
    """
    merger = SensorMerger()
    
    # Build dict of sensor CSVs
    sensor_csvs = {}
    for name in sensor_names:
        csv_path = individual_dir / f"{name}_10min.csv"
        if csv_path.exists():
            sensor_csvs[name] = csv_path
        else:
            logging.warning(f"CSV not found: {csv_path}")
    
    # Merge
    merged = merger.merge_sensors(sensor_csvs, start_date=start_date, end_date=end_date)
    
    # Also export monthly
    merger.export_monthly_merged(merged)
    
    return merged