#!/usr/bin/env python3
"""
Migration script: Move from flat to per-sensor directory structure.

Old structure:
    output/individual/
    ├── CO2_SCT1_2M_10min.csv
    ├── CO2_SCT1_2M_2024_09.csv
    ├── CO2_SCT1_2M_uptime.csv
    └── parquet/
        └── CO2_SCT1_2M_2024_09.parquet
    output/merged/
    └── SMEAR_EE_CO2_merged.csv

New structure:
    output/sensors/
    ├── CO2_SCT1_2M/
    │   ├── csv/
    │   │   ├── CO2_SCT1_2M_10min.csv
    │   │   ├── CO2_SCT1_2M_2024_09.csv
    │   │   └── CO2_SCT1_2M_uptime.csv
    │   ├── parquet/
    │   │   └── CO2_SCT1_2M_2024_09.parquet
    │   └── plots/
    └── ...
    output/merged/
    ├── csv/
    │   └── SMEAR_EE_CO2_merged.csv
    └── parquet/
        └── SMEAR_EE_CO2_2024_09_merged.parquet

Usage:
    python migrate_to_per_sensor.py --dry-run   # Preview changes
    python migrate_to_per_sensor.py             # Execute migration
    python migrate_to_per_sensor.py --rollback  # Undo migration
"""

import argparse
import shutil
import re
from pathlib import Path
from datetime import datetime


# Configuration
SENSOR_NAMES = [
    "CO2_SCT1_2M",
    "CO2_30M_A", 
    "CO2_30M_B",
    "CO2_30M_C",
    "LGR_30M"
]

OLD_INDIVIDUAL_DIR = Path("output/individual")
OLD_PARQUET_DIR = Path("output/individual/parquet")
OLD_MERGED_DIR = Path("output/merged")

NEW_SENSORS_DIR = Path("output/sensors")
NEW_MERGED_DIR = Path("output/merged")


def create_backup(dry_run: bool = False) -> Path:
    """Create timestamped backup of output directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"output_backup_{timestamp}")
    
    if dry_run:
        print(f"[DRY RUN] Would create backup at: {backup_dir}")
        return backup_dir
    
    if Path("output").exists():
        print(f"Creating backup at: {backup_dir}")
        shutil.copytree("output", backup_dir)
    
    return backup_dir


def migrate_sensor_files(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """
    Migrate per-sensor files to new structure.
    
    Returns list of (source, destination) moves.
    """
    moves = []
    
    for sensor in SENSOR_NAMES:
        # Create target directories
        sensor_csv_dir = NEW_SENSORS_DIR / sensor / "csv"
        sensor_pq_dir = NEW_SENSORS_DIR / sensor / "parquet"
        sensor_plots_dir = NEW_SENSORS_DIR / sensor / "plots"
        
        if not dry_run:
            sensor_csv_dir.mkdir(parents=True, exist_ok=True)
            sensor_pq_dir.mkdir(parents=True, exist_ok=True)
            sensor_plots_dir.mkdir(parents=True, exist_ok=True)
        
        # Move CSV files
        if OLD_INDIVIDUAL_DIR.exists():
            # Main 10min CSV
            main_csv = OLD_INDIVIDUAL_DIR / f"{sensor}_10min.csv"
            if main_csv.exists():
                dest = sensor_csv_dir / main_csv.name
                moves.append((main_csv, dest))
            
            # Uptime CSV
            uptime_csv = OLD_INDIVIDUAL_DIR / f"{sensor}_uptime.csv"
            if uptime_csv.exists():
                dest = sensor_csv_dir / uptime_csv.name
                moves.append((uptime_csv, dest))
            
            # Monthly CSVs (pattern: SENSOR_YYYY_MM.csv)
            for csv_file in OLD_INDIVIDUAL_DIR.glob(f"{sensor}_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"):
                dest = sensor_csv_dir / csv_file.name
                moves.append((csv_file, dest))
        
        # Move parquet files
        if OLD_PARQUET_DIR.exists():
            for pq_file in OLD_PARQUET_DIR.glob(f"{sensor}_*.parquet"):
                dest = sensor_pq_dir / pq_file.name
                moves.append((pq_file, dest))
    
    return moves


def migrate_merged_files(dry_run: bool = False) -> list[tuple[Path, Path]]:
    """
    Migrate merged files to new structure.
    
    Returns list of (source, destination) moves.
    """
    moves = []
    
    # Create target directories
    merged_csv_dir = NEW_MERGED_DIR / "csv"
    merged_pq_dir = NEW_MERGED_DIR / "parquet"
    
    if not dry_run:
        merged_csv_dir.mkdir(parents=True, exist_ok=True)
        merged_pq_dir.mkdir(parents=True, exist_ok=True)
    
    if OLD_MERGED_DIR.exists():
        # Move merged CSVs
        for csv_file in OLD_MERGED_DIR.glob("*.csv"):
            dest = merged_csv_dir / csv_file.name
            moves.append((csv_file, dest))
        
        # Move merged parquets (if in old merged/parquet/)
        old_merged_pq = OLD_MERGED_DIR / "parquet"
        if old_merged_pq.exists():
            for pq_file in old_merged_pq.glob("*.parquet"):
                dest = merged_pq_dir / pq_file.name
                moves.append((pq_file, dest))
    
    return moves


def execute_moves(moves: list[tuple[Path, Path]], dry_run: bool = False):
    """Execute file moves."""
    for src, dst in moves:
        # Skip if source and destination are identical
        if src.resolve() == dst.resolve():
            if dry_run:
                print(f"  [SKIP] {src} (already in place)")
            continue
        
        if dry_run:
            print(f"  [DRY RUN] {src} → {dst}")
        else:
            print(f"  Moving: {src} → {dst}")
            shutil.move(str(src), str(dst))


def cleanup_empty_dirs(dry_run: bool = False):
    """Remove empty directories after migration."""
    dirs_to_check = [
        OLD_PARQUET_DIR,
        OLD_INDIVIDUAL_DIR,
    ]
    
    for d in dirs_to_check:
        if d.exists() and not any(d.iterdir()):
            if dry_run:
                print(f"  [DRY RUN] Would remove empty directory: {d}")
            else:
                print(f"  Removing empty directory: {d}")
                d.rmdir()


def run_migration(dry_run: bool = False):
    """Run full migration."""
    print("=" * 60)
    print("SMEAR Estonia Sensor Data Migration")
    print("Flat → Per-Sensor Directory Structure")
    print("=" * 60)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be moved\n")
    else:
        # Create backup first
        backup_dir = create_backup(dry_run=False)
        print(f"✓ Backup created: {backup_dir}\n")
    
    # Migrate sensor files
    print("Migrating sensor files...")
    sensor_moves = migrate_sensor_files(dry_run=dry_run)
    execute_moves(sensor_moves, dry_run=dry_run)
    print(f"  {len(sensor_moves)} sensor files {'would be moved' if dry_run else 'moved'}\n")
    
    # Migrate merged files
    print("Migrating merged files...")
    merged_moves = migrate_merged_files(dry_run=dry_run)
    execute_moves(merged_moves, dry_run=dry_run)
    print(f"  {len(merged_moves)} merged files {'would be moved' if dry_run else 'moved'}\n")
    
    # Cleanup
    print("Cleaning up empty directories...")
    cleanup_empty_dirs(dry_run=dry_run)
    
    # Summary
    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN COMPLETE")
        print(f"Total files that would be moved: {len(sensor_moves) + len(merged_moves)}")
        print("\nRun without --dry-run to execute migration.")
    else:
        print("MIGRATION COMPLETE")
        print(f"Total files moved: {len(sensor_moves) + len(merged_moves)}")
        print(f"\nBackup available at: {backup_dir}")
        print("To rollback, run: python migrate_to_per_sensor.py --rollback")
    print("=" * 60)


def run_rollback():
    """Find most recent backup and restore it."""
    backups = sorted(Path(".").glob("output_backup_*"))
    
    if not backups:
        print("ERROR: No backup directories found")
        return
    
    latest_backup = backups[-1]
    print(f"Rolling back to: {latest_backup}")
    
    # Remove current output
    if Path("output").exists():
        shutil.rmtree("output")
    
    # Restore backup
    shutil.copytree(latest_backup, "output")
    print("✓ Rollback complete")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate SMEAR sensor data to per-sensor directory structure"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Preview changes without moving files"
    )
    parser.add_argument(
        "--rollback",
        action="store_true", 
        help="Restore from most recent backup"
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        run_rollback()
    else:
        run_migration(dry_run=args.dry_run)


if __name__ == "__main__":
    main()