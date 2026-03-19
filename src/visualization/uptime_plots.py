"""Uptime visualization tools

All uptime plots follow the same pattern:
1. Load uptime CSV
2. Calculate daily/monthly aggregates
3. Create matplotlib figure
4. Save with consistent naming
"""

from pathlib import Path
from typing import Dict
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .base_plotter import BasePlotter
import numpy as np
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm


class UptimePlots(BasePlotter):
    """Generate uptime analysis plots"""
    
    def plot_timeseries(
        self,
        uptime_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot daily uptime percentage over time.
        
        Creates a line plot showing uptime percentage for each day, with markers
        highlighting days below 95% threshold. Useful for identifying sensor
        downtime periods and maintenance needs.
        
        Args:
            uptime_csv: Path to uptime log CSV file (e.g., CO2_30M_A_uptime.csv)
            sensor_name: Sensor name for plot title and filename
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the plot
        """
        df = pd.read_csv(uptime_csv)
        
        # Parse dates
        df['start'] = pd.to_datetime(df['start'], errors='coerce')
        df['date'] = df['start'].dt.floor('D')
        df['uptime_pct'] = df['uptime_ratio'] * 100
        
        # Drop invalid dates
        df = df.dropna(subset=['date'])
        
        # Reindex to full date range so that missing days become NaN
        full_range = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
        daily = df.groupby('date')['uptime_pct'].mean()
        daily = daily.reindex(full_range)  # gaps become NaN → line breaks
        
        # Create plot 
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Plot with markers ...line breaks naturally at NaN gaps
        ax.plot(daily.index, daily.values, marker='o', linewidth=1.5, 
                markersize=4, color='steelblue', label='Daily Uptime')
        
        # Add 95% threshold line
        ax.axhline(95, color='red', linestyle='--', linewidth=1, 
                   alpha=0.7, label='95% Threshold')
        
        # Highlight low-uptime days
        low_uptime = df[df['uptime_pct'] < 95]
        if not low_uptime.empty:
            ax.scatter(low_uptime['date'], low_uptime['uptime_pct'],
                      color='red', s=50, zorder=5, alpha=0.7,
                      label=f'Low Uptime Days (n={len(low_uptime)})')
        
        # Styling
        ax.set_ylabel('Uptime (%)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_title(f'{sensor_name}: Daily Uptime', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='lower left')
        
        # Format x-axis
        fig.autofmt_xdate()
        
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_uptime_timeseries.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_heatmap(
        self,
        uptime_csv: Path,
        sensor_name: str,
        save: bool = True
    ) -> plt.Figure:
        """
        Plot uptime as monthly heatmap (calendar view).
        
        Creates a heatmap showing uptime ratio for each day of each month.
        Colors range from red (low uptime) to green (high uptime). Useful
        for visualizing seasonal patterns and identifying problem periods.
        
        Args:
            uptime_csv: Path to uptime log CSV file
            sensor_name: Sensor name for plot title and filename
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object containing the heatmap
        """
        df = pd.read_csv(uptime_csv)
        
        # Build a sortable year-month key and a readable label
        df['ym_sort'] = df['year'] * 100 + df['month'] # e.g. 202409
        df['ym_label'] = df.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1) # e.g. "2024-09"

        # pivoting on labels; days = columns
        pivot = df.pivot_table(
            index='ym_label',
            columns='day',
            values='uptime_ratio',
            aggfunc='mean'
        )

        # Sort chronologically using the numeric key
        sort_order = (
            df.drop_duplicates('ym_label')
            .sort_values('ym_sort')['ym_label']
            .tolist()
        )
        
        pivot = pivot.reindex(sort_order)

        # Plot... heatmap renders index top-to-bottom: earliest month = top (reading order)
        fig, ax = plt.subplots(figsize=(16, max(6, len(pivot) * 0.6)))
        
        sns.heatmap(
            pivot,
            cmap='RdYlGn',
            vmin=0,
            vmax=1,
            linewidths=0.5,
            cbar_kws={'label': 'Uptime Ratio'},
            ax=ax
        )
        
        ax.set_title(f'{sensor_name}: Uptime Heatmap', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Day of Month', fontsize=12)
        ax.set_ylabel('Month', fontsize=12)
        
        plt.tight_layout()
        
        if save:
            filename = f"{sensor_name}_uptime_heatmap.png"
            self._save_figure(fig, filename)
        
        return fig
    
    def plot_summary(
        self,
        uptime_csvs: Dict[str, Path],
        save: bool = True
    ) -> plt.Figure:
        """
        Multi-sensor uptime comparison.
        
        Creates a two-panel plot comparing uptime statistics across sensors:
        - Left panel: Mean uptime percentage per sensor
        - Right panel: Number of days below 95% threshold per sensor
        
        Args:
            uptime_csvs: Dict mapping sensor names to uptime CSV paths
                         Example: {'CO2_30M_A': Path('CO2_30M_A_uptime.csv'), ...}
            save: If True, save plot to output_dir as PNG (default: True)
            
        Returns:
            matplotlib Figure object with two subplots
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        stats = []
        for sensor_name, csv_path in uptime_csvs.items():
            df = pd.read_csv(csv_path)
            stats.append({
                'sensor': sensor_name,
                'mean_uptime': df['uptime_ratio'].mean() * 100,
                'median_uptime': df['uptime_ratio'].median() * 100,
                'min_uptime': df['uptime_ratio'].min() * 100,
                'days_below_95': (df['uptime_ratio'] < 0.95).sum()
            })
        
        stats_df = pd.DataFrame(stats)
        
        # Bar chart of mean uptime
        ax1.bar(stats_df['sensor'], stats_df['mean_uptime'], 
                color='steelblue', alpha=0.8)
        ax1.axhline(95, color='red', linestyle='--', linewidth=1, alpha=0.7)
        ax1.set_ylabel('Mean Uptime (%)', fontsize=12)
        ax1.set_title('Average Uptime by Sensor', fontsize=14, fontweight='bold')
        ax1.set_ylim(0, 105)
        ax1.grid(axis='y', alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Bar chart of days below 95%
        ax2.bar(stats_df['sensor'], stats_df['days_below_95'],
                color='coral', alpha=0.8)
        ax2.set_ylabel('Days Below 95% Uptime', fontsize=12)
        ax2.set_title('Low-Uptime Days by Sensor', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        
        if save:
            filename = "uptime_summary_all_sensors.png"
            self._save_figure(fig, filename)
        
        return fig

    def plot_coverage_overlap(
        self,
        merged_uptime_csv: Path,
        trim_mode: str = "auto", 
        # "none"   — show all months
        # "auto"   — drop leading/trailing months with zero SCD41 activity
        # "manual" — crop to trim_start / trim_end (inclusive, "YYYY-MM")
        trim_start: str | None = None,
        trim_end: str | None = None,
        show_lgr_absence: bool = True,
        save: bool = True) -> plt.Figure:
        """
        Plot a calendar heatmap showing SCD41 sensor coverage overlap.

        Reads the merged uptime CSV to build a month × day grid where each
        cell is coloured by the number of SCD41 sensors reporting on that day.
        Optionally overlays hatching on days where the LGR reference instrument
        was absent.  Supports three trim modes to remove months outside the
        active deployment window.

        Args:
            merged_uptime_csv: Path to the merged uptime CSV produced by the
                               pipeline (e.g., SMEAR_EE_CO2_uptime_merged.csv).
                               Must contain 'year', 'month', 'day',
                               'scd_reporting', and optionally 'ref_reporting'.
            trim_mode: Controls which months are shown.
                       'auto'   — drop leading/trailing months with zero SCD41
                                  activity (default).
                       'none'   — show the full date range in the CSV.
                       'manual' — restrict to trim_start..trim_end (inclusive).
            trim_start: Start month in 'YYYY-MM' format; used only when
                        trim_mode is 'manual'.
            trim_end: End month in 'YYYY-MM' format; used only when
                      trim_mode is 'manual'.
            show_lgr_absence: If True, overlay red hatching on days where the
                              LGR reference was not reporting (default: True).
            save: If True, save the figure to output_dir as
                  'uptime_overlay_count.png' (default: True).

        Returns:
            matplotlib Figure object containing the coverage overlap heatmap.
        """

        SHOW_LGR_ABSENCE = show_lgr_absence

        # --- Load & identify columns ---
        df = pd.read_csv(merged_uptime_csv)
        df["date"] = pd.to_datetime(df[["year", "month", "day"]])
        df["ym"] = df["date"].dt.to_period("M")

        # Auto-detect sensor columns (everything that isn't scaffolding)
        SCAFFOLD = {"year", "month", "day", "date", "ym", "scd_reporting", "ref_reporting"}
        REF_COL = next((c for c in df.columns if "lgr" in c.lower()), None)
        if REF_COL:
            SCAFFOLD.add(REF_COL)
        SCD_SENSORS = [c for c in df.columns if c not in SCAFFOLD]
        self.logger.info(f"SCD41 sensors detected: {SCD_SENSORS}")
        self.logger.info(f"Reference column: {REF_COL}")

        # --- Apply trim ---
        if trim_mode == "auto":
            monthly_max = df.groupby("ym")["scd_reporting"].max()
            active = monthly_max[monthly_max > 0].index
            if len(active) > 0:
                df = df[(df["ym"] >= active.min()) & (df["ym"] <= active.max())]
                self.logger.info(f"Auto-trimmed to {active.min()} .. {active.max()}")
        elif trim_mode == "manual":
            start_p = pd.Period(trim_start, freq="M")
            end_p = pd.Period(trim_end, freq="M")
            df = df[(df["ym"] >= start_p) & (df["ym"] <= end_p)]
            self.logger.info(f"Manual trim to {trim_start} .. {trim_end}")

        months = sorted(df["ym"].unique())
        month_labels = [str(m) for m in months]
        n_months = len(months)
        
        # --- Shared grids ---
        scd_grid = np.full((n_months, 31), np.nan)
        for i, m in enumerate(months):
            chunk = df[df["ym"] == m]
            days = chunk["day"].values.astype(int) - 1
            scd_grid[i, days] = chunk["scd_reporting"].values

        lgr_grid = None
        if "ref_reporting" in df.columns:
            lgr_grid = np.full((n_months, 31), False)
            for i, m in enumerate(months):
                chunk = df[df["ym"] == m]
                days = chunk["day"].values.astype(int) - 1
                lgr_grid[i, days] = ~chunk["ref_reporting"].astype(bool).values

        OVERLAP_COLOURS = ["#e0e0e0", "#c7e9c0", "#74c476", "#238b45", "#00441b"]
        CMAP_COUNT = ListedColormap(OVERLAP_COLOURS[:len(SCD_SENSORS) + 1])
        bounds = [i - 0.5 for i in range(len(SCD_SENSORS) + 2)]
        NORM_COUNT = BoundaryNorm(bounds, CMAP_COUNT.N)

        fig, ax = plt.subplots(figsize=(14, max(4, n_months * 0.45)), constrained_layout=True)

        masked = np.ma.masked_invalid(scd_grid)
        mesh = ax.pcolormesh(
            np.arange(32) - 0.5,
            np.arange(n_months + 1) - 0.5,
            masked,
            cmap=CMAP_COUNT, norm=NORM_COUNT,
            edgecolors="white", linewidth=0.5,
        )

        if SHOW_LGR_ABSENCE and lgr_grid is not None:
            for i in range(n_months):
                for j in range(31):
                    if lgr_grid[i, j]:
                        ax.add_patch(plt.Rectangle(
                            (j - 0.5, i - 0.5), 1, 1,
                            fill=False, hatch="///",
                            edgecolor="#d62728", linewidth=1.2,
                        ))

        ax.set_xticks(range(31))
        ax.set_xticklabels(range(1, 32), fontsize=8)
        ax.set_xlabel("Day of Month")
        ax.set_yticks(range(n_months))
        ax.set_yticklabels(month_labels, fontsize=9)
        ax.set_ylabel("Month")
        ax.set_title("SCD41 Sensor Coverage Overlap", fontsize=13, fontweight="bold", pad=10)
        ax.invert_yaxis()

        cbar = fig.colorbar(mesh, ax=ax, ticks=range(len(SCD_SENSORS) + 1), shrink=0.6, aspect=20, pad=0.02)
        cbar.set_label("SCD41 Sensors Reporting", fontsize=10)
        cbar.ax.set_yticklabels([str(i) for i in range(len(SCD_SENSORS) + 1)])

        if SHOW_LGR_ABSENCE and lgr_grid is not None and lgr_grid.any():
            ax.legend(
                handles=[mpatches.Patch(
                    facecolor="none", edgecolor="#d62728",
                    hatch="///", label="LGR reference absent",
                )],
                loc="lower right", fontsize=9,
            )

        if save:
            self._save_figure(fig, "uptime_overlay_count.png")
        
        return fig
