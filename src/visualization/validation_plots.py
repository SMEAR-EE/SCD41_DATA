"""CO2 validation visualization tools

Compare test sensors against reference measurements.
Includes timeseries, scatter plots, and difference analyses.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from .base_plotter import BasePlotter


class ValidationPlots(BasePlotter):
    """Generate validation plots comparing sensors"""
    
    def plot_timeseries(
        self,
        data_csvs: Dict[str, Path],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot CO2 timeseries for multiple sensors.
        
        Overlays CO2 measurements from multiple sensors on a single plot for
        visual comparison of temporal patterns. Useful for identifying sensor
        drift, calibration issues, or measurement inconsistencies.
        
        Args:
            data_csvs: Dict mapping sensor names to 10min CSV paths
                       Example: {'LGR_30M': Path('LGR_30M_10min.csv'), ...}
            start_date: Optional start date filter in 'YYYY-MM-DD' format
            end_date: Optional end date filter in 'YYYY-MM-DD' format
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the timeseries plot
        """
        fig, ax = plt.subplots(figsize=(16, 6))
        
        for sensor_name, csv_path in data_csvs.items():
            # df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            df = pd.read_csv(csv_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
            
            # Filter date range
            if start_date:
                df = df[df['timestamp'] >= start_date]
            if end_date:
                df = df[df['timestamp'] <= end_date]
            
            # Get CO2 column
            co2_col = self._detect_co2_column(df)
            
            # Plot
            ax.plot(df['timestamp'], df[co2_col], label=sensor_name,
                    alpha=0.7, marker='.', markersize=1.5, linewidth=0.8)
        
        ax.set_ylabel('CO₂ (ppm)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title('CO₂ Timeseries Comparison', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            filename = "co2_timeseries_comparison.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_scatter(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str,
        test_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Scatter plot: reference vs test sensor.
        
        Creates a scatter plot comparing test sensor measurements against
        reference sensor measurements. Includes 1:1 line and validation
        statistics (correlation, RMSE, bias, sample count).
        
        Args:
            reference_csv: Path to reference sensor 10min CSV (e.g., LGR)
            test_csv: Path to test sensor 10min CSV (e.g., SCD41)
            reference_name: Reference sensor name for axis labels
            test_name: Test sensor name for axis labels
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the scatter plot, or None if
            no overlapping data exists between sensors
        """
        # Load data
        # ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref = pd.read_csv(reference_csv)
        ref['timestamp'] = pd.to_datetime(ref['timestamp'], format='mixed')
        # test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv)
        test['timestamp'] = pd.to_datetime(test['timestamp'], format='mixed')
        
        # Get CO2 columns
        ref_col = self._detect_co2_column(ref)
        test_col = self._detect_co2_column(test)
        
        # Merge on timestamp
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        ).dropna()
        
        if len(merged) == 0:
            self.logger.warning(f"No overlapping data between {reference_name} and {test_name}")
            return None
        
        # Calculate stats
        corr = np.corrcoef(merged[ref_col], merged[test_col])[0, 1]
        rmse = np.sqrt(np.mean((merged[ref_col] - merged[test_col])**2))
        bias = np.mean(merged[test_col] - merged[ref_col])
        
        # Create plot
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Scatter
        ax.scatter(merged[ref_col], merged[test_col], 
                  alpha=0.5, s=10, color='steelblue')
        
        # 1:1 line
        min_val = min(merged[ref_col].min(), merged[test_col].min())
        max_val = max(merged[ref_col].max(), merged[test_col].max())
        ax.plot([min_val, max_val], [min_val, max_val], 
               'r--', linewidth=2, label='1:1 Line')
        
        # Stats text
        stats_text = f'R = {corr:.3f}\nRMSE = {rmse:.2f} ppm\nBias = {bias:.2f} ppm\nn = {len(merged)}'
        ax.text(0.70, 0.20, stats_text, transform=ax.transAxes,
               fontsize=11, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Styling
        ax.set_xlabel(f'{reference_name} CO₂ (ppm)', fontsize=12)
        ax.set_ylabel(f'{test_name} CO₂ (ppm)', fontsize=12)
        ax.set_title(f'Scatter: {test_name} vs {reference_name}',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        
        if save:
            filename = f"scatter_{test_name}_vs_{reference_name}.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_difference(
        self,
        reference_csv: Path,
        test_csv: Path,
        reference_name: str,
        test_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot difference (test - reference) over time.
        
        Creates a two-panel plot for bias analysis:
        - Top panel: Difference timeseries with zero line and mean bias
        - Bottom panel: Histogram of differences showing distribution
        
        Useful for identifying systematic bias, drift over time, and
        outliers in sensor measurements.
        
        Args:
            reference_csv: Path to reference sensor 10min CSV
            test_csv: Path to test sensor 10min CSV
            reference_name: Reference sensor name for labels
            test_name: Test sensor name for labels
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object with two subplots, or None if no
            overlapping data exists between sensors
        """
        # Load data
        # ref = pd.read_csv(reference_csv, parse_dates=['timestamp'])
        ref = pd.read_csv(reference_csv)
        ref['timestamp'] = pd.to_datetime(ref['timestamp'], format='mixed')
        # test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv)
        test['timestamp'] = pd.to_datetime(test['timestamp'], format='mixed')
        
        # Get CO2 columns
        ref_col = self._detect_co2_column(ref)
        test_col = self._detect_co2_column(test)
        
        # Merge on timestamp
        merged = pd.merge(
            ref[['timestamp', ref_col]],
            test[['timestamp', test_col]],
            on='timestamp',
            how='inner'
        ).dropna()
        
        if len(merged) == 0:
            self.logger.warning(f"No overlapping data between {reference_name} and {test_name}")
            return None
        
        # Calculate difference
        merged['diff'] = merged[test_col] - merged[ref_col]
        
        # Stats
        mean_diff = merged['diff'].mean()
        std_diff = merged['diff'].std()
        
        # Create 2-panel plot
        fig = plt.figure(figsize=(16, 8))
        gs = GridSpec(2, 1, height_ratios=[2, 1])
        
        # Panel 1: Timeseries
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(merged['timestamp'], merged['diff'], 
                color='steelblue', alpha=0.7, linewidth=0.8,
                marker='.', markersize=1.5)
        ax1.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax1.axhline(mean_diff, color='green', linestyle='-', linewidth=1.5, alpha=0.7,
                   label=f'Mean = {mean_diff:.2f} ppm')
        ax1.fill_between(merged['timestamp'],
                        mean_diff - std_diff,
                        mean_diff + std_diff,
                        color='green', alpha=0.2, label=f'±1σ = {std_diff:.2f} ppm')
        
        ax1.set_ylabel('Difference (ppm)', fontsize=12)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_title(f'Difference: {test_name} - {reference_name}',
                     fontsize=14, fontweight='bold')
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Format date tick labels on the timeseries panel
        ax1.tick_params(axis='x', rotation=30)
        
        # Panel 2: Histogram
        ax2 = fig.add_subplot(gs[1])
        ax2.hist(merged['diff'], bins=50, color='steelblue', alpha=0.7, edgecolor='black')
        ax2.axvline(0, color='red', linestyle='--', linewidth=1.5)
        ax2.axvline(mean_diff, color='green', linestyle='-', linewidth=1.5)
        ax2.set_xlabel('Difference (ppm)', fontsize=12)
        ax2.set_ylabel('Count', fontsize=12)
        ax2.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filename = f"difference_{test_name}_vs_{reference_name}.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_co2_timeseries(
        self,
        data: 'Path | pd.DataFrame',
        sensor_name: str,
        period_label: Optional[str] = None,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot CO2 timeseries for a single sensor with summary statistics.
        
        Creates a timeseries of CO2 readings annotated with mean, std,
        min/max, and sample count. Works for both full datasets and
        monthly subsets.
        
        Args:
            data: Path to sensor CSV file, or a pre-loaded DataFrame
                  (must contain 'timestamp' and a recognised CO2 column)
            sensor_name: Sensor name for title and filename
            period_label: Optional period label (e.g., '2024_09') appended
                          to filename. If None, uses 'full'.
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object, or None if no CO2 data found
        """
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            # df = pd.read_csv(data, parse_dates=['timestamp'])
            df = pd.read_csv(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='mixed')
        try:
            co2_col = self._detect_co2_column(df)
        except ValueError:
            self.logger.warning("No CO2 column in data for %s", sensor_name)
            return None
        
        co2 = df[['timestamp', co2_col]].dropna()
        
        if co2.empty:
            self.logger.warning("No valid CO2 data for %s", sensor_name)
            return None
        
        # Statistics
        vals = co2[co2_col]
        stats = {
            'mean': vals.mean(),
            'std': vals.std(),
            'min': vals.min(),
            'max': vals.max(),
            'n': len(vals),
        }
        
        # Create plot
        fig, ax = plt.subplots(figsize=(14, 6))
        
        ax.plot(co2['timestamp'], vals,
                color='steelblue', alpha=0.8, linewidth=0.8,
                marker='.', markersize=2,
                label=sensor_name)
        
        # Mean line
        ax.axhline(stats['mean'], color='green', linestyle='-',
                   linewidth=1.5, alpha=0.7,
                   label=f"Mean = {stats['mean']:.1f} ppm")
        
        # +/- 1 std band
        ax.fill_between(
            co2['timestamp'],
            stats['mean'] - stats['std'],
            stats['mean'] + stats['std'],
            color='green', alpha=0.1,
            label=f"\u00b11\u03c3 = {stats['std']:.1f} ppm")
        
        # Stats annotation
        stats_text = (f"n = {stats['n']}\n"
                      f"Mean = {stats['mean']:.1f} ppm\n"
                      f"\u03c3 = {stats['std']:.1f} ppm\n"
                      f"Range = [{stats['min']:.0f}, {stats['max']:.0f}] ppm")
        ax.text(0.98, 0.95, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Styling
        title = f'{sensor_name}: CO\u2082 Timeseries'
        if period_label:
            title += f' ({period_label})'
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('CO\u2082 (ppm)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        fig.autofmt_xdate()
        plt.tight_layout()
        
        if save:
            suffix = period_label if period_label else 'full'
            filename = f"{sensor_name}_co2_timeseries_{suffix}.png"
            self._save_figure(fig, filename)
        
        return fig

    # ── Merged-data panel plots (hue-mapped) ────────────────────────

    def plot_scatter_panel_hue(
        self,
        merged: 'Path | pd.DataFrame',
        lgr_co2_col: str,
        sensors: List[Dict[str, str]],
        hue_var: str = "temp",
        cmap: str = "RdYlBu_r",
        save: bool = True,
    ) -> plt.Figure:
        """
        2x2 scatter grid of LGR vs each SCD41 sensor, coloured by
        temperature or relative humidity.

        Each panel shows one test sensor against the LGR reference with
        a 1:1 line and validation statistics (R, RMSE, bias, n).
        A shared colourbar ensures consistent mapping across panels.

        Args:
            merged: Path to merged CSV or pre-loaded DataFrame.
                    Must contain timestamp, LGR CO2, and per-sensor
                    CO2 / temp / humidity columns.
            lgr_co2_col: Column name for LGR reference CO2 in the
                         merged data (e.g. 'lgr_30m_CO2_dry_mean').
            sensors: List of dicts, one per sensor, each with keys:
                     'co2', 'temp', 'rh' (column names) and 'label'
                     (display name).  Order determines panel position
                     (top-left → top-right → bottom-left → bottom-right).
            hue_var: Which environmental variable to colour by.
                     Must be 'temp' or 'rh' (default: 'temp').
            cmap: Matplotlib colourmap name (default: 'RdYlBu_r').
            save: If True, save plot to output_dir (default: True).

        Returns:
            matplotlib Figure, or None if fewer than 1 sensor has data.
        """
        df = self._load_merged(merged)

        hue_label = (
            "Temperature (\u00b0C)" if hue_var == "temp"
            else "Relative Humidity (%)"
        )

        # Global hue range (2nd–98th percentile) for consistent colour scale
        all_hue = pd.concat(
            df.loc[
                df[lgr_co2_col].notna()
                & df[s["co2"]].notna()
                & df[s[hue_var]].notna(),
                s[hue_var],
            ]
            for s in sensors
        )
        if all_hue.empty:
            self.logger.warning("No overlapping data for scatter panel")
            return None
        vmin, vmax = np.nanpercentile(all_hue, [2, 98])

        n_sensors = len(sensors)
        ncols = min(n_sensors, 2)
        nrows = (n_sensors + 1) // 2
        fig, axes = plt.subplots(
            nrows, ncols, figsize=(6 * ncols, 5.5 * nrows)
        )
        if n_sensors == 1:
            axes = [axes]
        else:
            axes = axes.ravel()

        sc = None
        for ax, info in zip(axes, sensors):
            co2_col = info["co2"]
            hue_col = info[hue_var]

            mask = (
                df[lgr_co2_col].notna()
                & df[co2_col].notna()
                & df[hue_col].notna()
            )
            sub = df.loc[mask]

            if len(sub) == 0:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                        ha="center", va="center", fontsize=12, color="gray")
                ax.set_title(info["label"], fontsize=12, fontweight="bold")
                ax.set_xlabel("LGR CO\u2082 (ppm)", fontsize=10)
                ax.set_ylabel(f"{info['label']} CO\u2082 (ppm)", fontsize=10)
                ax.set_xticks([])
                ax.set_yticks([])
                continue

            ref = sub[lgr_co2_col].values
            test = sub[co2_col].values
            hue = sub[hue_col].values

            corr = np.corrcoef(ref, test)[0, 1]
            rmse = np.sqrt(np.mean((ref - test) ** 2))
            bias = np.mean(test - ref)

            sc = ax.scatter(
                ref, test, c=hue, cmap=cmap, vmin=vmin, vmax=vmax,
                s=6, alpha=0.5, edgecolors="none", rasterized=True,
            )

            lo = min(ref.min(), test.min())
            hi = max(ref.max(), test.max())
            ax.plot([lo, hi], [lo, hi], "k--", lw=1.2, alpha=0.6)

            stats_txt = (
                f"R = {corr:.3f}\n"
                f"RMSE = {rmse:.1f} ppm\n"
                f"Bias = {bias:+.1f} ppm\n"
                f"n = {len(sub):,}"
            )
            ax.text(
                0.04, 0.96, stats_txt, transform=ax.transAxes,
                fontsize=9, va="top", ha="left",
                bbox=dict(
                    boxstyle="round,pad=0.3", fc="white",
                    ec="gray", alpha=0.85,
                ),
            )

            ax.set_xlabel("LGR CO\u2082 (ppm)", fontsize=10)
            ax.set_ylabel(f"{info['label']} CO\u2082 (ppm)", fontsize=10)
            ax.set_title(info["label"], fontsize=12, fontweight="bold")
            ax.set_aspect("equal", adjustable="box")
            ax.grid(True, alpha=0.25)

        # Hide unused axes when sensor count is odd
        for ax in axes[n_sensors:]:
            ax.set_visible(False)

        if sc is None:
            self.logger.warning("No data rendered in scatter panel")
            plt.close(fig)
            return None

        fig.subplots_adjust(right=0.88, hspace=0.30, wspace=0.30)
        cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
        cbar = fig.colorbar(sc, cax=cbar_ax)
        cbar.set_label(hue_label, fontsize=11)

        fig.suptitle(
            f"LGR vs SCD41 \u2014 coloured by {hue_label.lower()}",
            fontsize=14, fontweight="bold", y=0.98,
        )

        if save:
            filename = f"scatter_panel_{hue_var}_hue.png"
            self._save_figure(fig, filename)

        return fig

    def plot_timeseries_hue(
        self,
        merged: 'Path | pd.DataFrame',
        lgr_co2_col: str,
        sensors: List[Dict[str, str]],
        hue_var: str = "temp",
        cmap: str = "RdYlBu_r",
        save: bool = True,
    ) -> plt.Figure:
        """
        Stacked timeseries panels (one per sensor) as scatter points
        coloured by temperature or relative humidity, with LGR reference
        overlaid as a thin grey line.

        Uses scatter markers rather than connected lines so the colour
        mapping remains readable.

        Args:
            merged: Path to merged CSV or pre-loaded DataFrame.
            lgr_co2_col: Column name for LGR reference CO2.
            sensors: List of dicts with keys 'co2', 'temp', 'rh', 'label'.
            hue_var: 'temp' or 'rh' (default: 'temp').
            cmap: Matplotlib colourmap name (default: 'RdYlBu_r').
            save: If True, save plot to output_dir (default: True).

        Returns:
            matplotlib Figure, or None if no sensor has data.
        """
        df = self._load_merged(merged)

        hue_label = (
            "Temperature (\u00b0C)" if hue_var == "temp"
            else "Relative Humidity (%)"
        )

        # Global hue range
        all_hue = pd.concat(
            df.loc[df[s["co2"]].notna() & df[s[hue_var]].notna(), s[hue_var]]
            for s in sensors
        )
        if all_hue.empty:
            self.logger.warning("No data for timeseries hue plot")
            return None
        vmin, vmax = np.nanpercentile(all_hue, [2, 98])

        n_sensors = len(sensors)
        fig, axes = plt.subplots(
            n_sensors, 1, figsize=(16, 3.5 * n_sensors), sharex=True,
        )
        if n_sensors == 1:
            axes = [axes]

        sc = None
        for ax, info in zip(axes, sensors):
            co2_col = info["co2"]
            hue_col = info[hue_var]

            mask = df[co2_col].notna() & df[hue_col].notna()
            sub = df.loc[mask]

            if len(sub) == 0:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                        ha="center", va="center", fontsize=12, color="gray")
                ax.set_ylabel("CO\u2082 (ppm)", fontsize=10)
                ax.set_title(info["label"], fontsize=11, fontweight="bold",
                             loc="left")
                ax.set_yticks([])
                continue

            sc = ax.scatter(
                sub["timestamp"], sub[co2_col],
                c=sub[hue_col], cmap=cmap, vmin=vmin, vmax=vmax,
                s=3, alpha=0.5, edgecolors="none", rasterized=True,
            )

            # LGR reference as grey backdrop
            lgr_mask = df[lgr_co2_col].notna()
            ax.plot(
                df.loc[lgr_mask, "timestamp"],
                df.loc[lgr_mask, lgr_co2_col],
                color="gray", alpha=0.3, lw=0.5, label="LGR (ref)",
            )

            ax.set_ylabel("CO\u2082 (ppm)", fontsize=10)
            ax.set_title(info["label"], fontsize=11, fontweight="bold",
                         loc="left")
            ax.grid(True, alpha=0.25)
            ax.legend(loc="upper right", fontsize=8, framealpha=0.8)

        axes[-1].set_xlabel("Date", fontsize=11)
        fig.autofmt_xdate()

        if sc is None:
            self.logger.warning("No data rendered in timeseries hue plot")
            plt.close(fig)
            return None

        fig.subplots_adjust(right=0.88, hspace=0.25)
        cbar_ax = fig.add_axes([0.90, 0.10, 0.02, 0.80])
        cbar = fig.colorbar(sc, cax=cbar_ax)
        cbar.set_label(hue_label, fontsize=11)

        fig.suptitle(
            f"CO\u2082 timeseries \u2014 coloured by {hue_label.lower()}",
            fontsize=14, fontweight="bold", y=0.98,
        )

        if save:
            filename = f"timeseries_{hue_var}_hue.png"
            self._save_figure(fig, filename)

        return fig

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _load_merged(merged: 'Path | pd.DataFrame') -> pd.DataFrame:
        """Load merged CSV or pass through a DataFrame."""
        if isinstance(merged, pd.DataFrame):
            return merged
        df = pd.read_csv(merged)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed")
        return df

    @staticmethod
    def build_sensor_map(
        merged_df: pd.DataFrame,
        sensor_names: List[str],
    ) -> Tuple[str, List[Dict[str, str]]]:
        """
        Auto-discover column mappings from merged CSV for a list of
        sensor names.

        Derives the merged-CSV column prefix from sensor_name by
        lower-casing and replacing the first underscore-delimited
        segment that looks like a height (e.g. '30M') with its
        lower-case form.  Then looks for '{prefix}_co2_mean',
        '{prefix}_temp_mean', '{prefix}_humidity_mean'.

        Also identifies the LGR reference CO2 column.

        Args:
            merged_df: The merged DataFrame (to validate columns exist).
            sensor_names: Pipeline sensor names, e.g.
                          ['CO2_SCT1_2M', 'CO2_30M_A', ...].

        Returns:
            (lgr_co2_col, sensors_list) where sensors_list is suitable
            for passing directly to plot_scatter_panel_hue /
            plot_timeseries_hue.

        Raises:
            ValueError: If no LGR CO2 column is found.
        """
        cols = set(merged_df.columns)

        # Discover LGR CO2 column
        lgr_candidates = [c for c in cols if c.startswith("lgr_") and "co2" in c.lower() and "dry_mean" in c.lower()]
        if not lgr_candidates:
            # Fallback: any lgr column with CO2 and mean
            lgr_candidates = [c for c in cols if c.startswith("lgr_") and "co2" in c.lower() and c.endswith("_mean")]
        if not lgr_candidates:
            raise ValueError(
                "No LGR CO2 column found in merged data. "
                f"Available columns starting with 'lgr_': "
                f"{[c for c in cols if c.startswith('lgr_')]}"
            )
        lgr_co2_col = lgr_candidates[0]

        # Build per-sensor mappings
        sensors = []
        for name in sensor_names:
            prefix = name.lower()  # e.g. 'co2_sct1_2m'
            co2_col = f"{prefix}_co2_mean"
            temp_col = f"{prefix}_temp_mean"
            rh_col = f"{prefix}_humidity_mean"

            if co2_col not in cols:
                continue  # skip sensors not present in merged data

            label = name.replace("CO2_SCT1_", "SCD41 ").replace("CO2_30M_", "SCD41 ")
            label = label.replace("2M", "2m")  # consistent lowercase height
            if "30M" in name.upper() or "30m" in name:
                label += " (30m)"

            sensors.append({
                "co2": co2_col,
                "temp": temp_col,
                "rh": rh_col,
                "label": label,
            })

        return lgr_co2_col, sensors