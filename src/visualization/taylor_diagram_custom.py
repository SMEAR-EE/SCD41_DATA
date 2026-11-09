"""Custom Taylor Diagram Implementation

A clean, controllable Taylor diagram for sensor validation and model comparison.
Based on Taylor (2001) but implemented from scratch for maximum flexibility.

Key advantages over SkillMetrics:
- Full control over styling and markers
- Handles any data range (no arbitrary limits)
- Easy to add many points on same diagram
- Publication-quality output
- No mysterious API issues

Reference: Taylor, K. E. (2001), Summarizing multiple aspects of model
performance in a single diagram, J. Geophys. Res., 106(D7), 7183-7192.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import matplotlib.transforms as transforms
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from .base_plotter import BasePlotter
import mpl_toolkits.axisartist.grid_finder as gf
import mpl_toolkits.axisartist.floating_axes as fa


class TaylorDiagram:
    """Taylor diagram using floating-axes polar projection.

    After Taylor (2001), J. Geophys. Res., 106(D7), 7183–7192.
    Uses mpl_toolkits.axisartist for proper axis formatting.

    Automatically extends to a semicircle when any correlation
    value is negative, so the diagram always fits the data.
    """

    def __init__(self, STD, fig=None, rect=111, label='_', smax=None,
                 extend_negative=False):
        """
        Initialise the Taylor diagram and draw the reference point and arc.

        Constructs a polar floating-axes figure using
        ``mpl_toolkits.axisartist``.  Correlation tick marks are placed at
        fixed values between −1 and 1 (negative ticks only when
        ``extend_negative=True``).  The reference standard deviation is plotted
        as a black star with a dashed arc at radius STD.

        Args:
            STD: Reference standard deviation (sets the scale of the diagram).
            fig: Existing matplotlib Figure to draw into, or None to create a
                 new one (default: None).
            rect: Subplot specification integer or tuple passed to
                  ``FloatingSubplot`` (default: 111).
            label: Legend label for the reference point (default: '_', which
                   hides it from the legend).
            smax: Maximum radial axis limit.  If None, defaults to
                  ``1.5 * STD`` (default: None).
            extend_negative: If True, extend the angular axis to a full
                             semicircle (correlation −1 to 1) to accommodate
                             negative correlations.  Use ``from_stats()`` to
                             set this automatically (default: False).

        Returns:
            None
        """
        self.STD = STD
        self.extend_negative = extend_negative
        tr = PolarAxes.PolarTransform(apply_theta_transforms=False)

        # Correlation tick positions
        rlocs_pos = np.array([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6,
                              0.7, 0.8, 0.9, 0.95, 0.99, 1.0])
        if extend_negative:
            rlocs_neg = np.array([-0.2, -0.4, -0.6, -0.8, -0.99])
            rlocs = np.concatenate((rlocs_neg[::-1], rlocs_pos))
            theta_max = np.pi
        else:
            rlocs = rlocs_pos
            theta_max = np.pi / 2

        tlocs = np.arccos(rlocs)
        gl1 = gf.FixedLocator(tlocs)
        tf1 = gf.DictFormatter(dict(zip(tlocs, map(str, rlocs))))

        self.smin = 0.001  # avoid duplicate 0.0 label at origin
        self.smax = smax if smax is not None else 1.5 * self.STD
        self.theta_max = theta_max

        gh = fa.GridHelperCurveLinear(
            tr,
            extremes=(0, theta_max, self.smin, self.smax),
            grid_locator1=gl1,
            tick_formatter1=tf1,
        )

        if fig is None:
            fig = plt.figure()

        ax = fa.FloatingSubplot(fig, rect, grid_helper=gh)
        fig.add_subplot(ax)

        # --- Axis configuration ---

        # Correlation axis (angular, along the arc)
        ax.axis['top'].set_axis_direction('bottom')
        ax.axis['top'].label.set_text("Correlation coefficient ($r$)")
        ax.axis['top'].toggle(ticklabels=True, label=True)
        ax.axis['top'].major_ticklabels.set_axis_direction('top')
        ax.axis['top'].label.set_axis_direction('top')

        # Bottom radial axis (horizontal, r=1 side)
        ax.axis['left'].set_axis_direction('bottom')
        ax.axis['left'].label.set_text("Standard Deviation (ppm)")
        ax.axis['left'].toggle(ticklabels=True, label=True)
        ax.axis['left'].major_ticklabels.set_axis_direction('bottom')
        ax.axis['left'].label.set_axis_direction('bottom')

        if extend_negative:
            # Left radial axis (vertical, r=-1 side) — mirror of right
            ax.axis['right'].set_axis_direction('top')
            ax.axis['right'].label.set_text("Standard Deviation (ppm)")
            ax.axis['right'].toggle(ticklabels=True, label=True)
            ax.axis['right'].major_ticklabels.set_axis_direction('bottom')
            ax.axis['right'].label.set_axis_direction('bottom')
            # ax.axis['right'].major_ticklabels.set_pad(0)
        else:
            # Standard quadrant: right axis is the vertical one
            ax.axis['right'].set_axis_direction('top')
            ax.axis['right'].label.set_text("Standard Deviation (ppm)")
            ax.axis['right'].toggle(ticklabels=True, label=True)
            ax.axis['right'].major_ticklabels.set_axis_direction('left')
            ax.axis['right'].label.set_axis_direction('top')
            # ax.axis['right'].major_ticklabels.set_pad(0)

        ax.axis['bottom'].set_visible(False)

        ax.grid(True, linestyle='-', color='#cccccc', linewidth=0.8)

        self._ax = ax
        self.ax = ax.get_aux_axes(tr)
        self.fig = fig

        # Reference point + std-dev arc
        (l,) = self.ax.plot([0], self.STD, 'k*', ls='', ms=12, label=label)
        t = np.linspace(0, theta_max)
        self.ax.plot(t, np.zeros_like(t) + self.STD, 'k--', linewidth=1.5,
                     label='_')

        self.samplePoints = [l]
        # Track off-chart points for proportional arrow scaling
        self._offchart_queue = []

    @classmethod
    def from_stats(cls, ref_std, correlations, fig=None, rect=111,
                   label='_', smax=None):
        """
        Factory method: create a diagram and auto-detect negative correlations.

        Inspects ``correlations`` and sets ``extend_negative=True`` if any
        value is below zero, ensuring the angular axis spans the full
        semicircle.

        Args:
            ref_std: Reference standard deviation.
            correlations: Iterable of correlation coefficients for the sensors
                          that will be plotted.  Used only to decide whether to
                          extend the axis; the values are not stored.
            fig: Existing matplotlib Figure or None (default: None).
            rect: Subplot specification (default: 111).
            label: Legend label for the reference point (default: '_').
            smax: Manual radial axis limit, or None to use ``1.5 * ref_std``
                  (default: None).

        Returns:
            TaylorDiagram instance configured for the supplied correlations.
        """
        extend = any(r < 0 for r in correlations)
        return cls(ref_std, fig=fig, rect=rect, label=label, smax=smax,
                   extend_negative=extend)

    def add_sample(self, STD, r, *args, **kwargs):
        """
        Plot a single sample point on the diagram.

        Converts the correlation coefficient ``r`` to an angle via
        ``arccos(r)`` and plots the point at polar coordinates
        ``(arccos(r), STD)``.  All additional positional and keyword arguments
        are forwarded to ``ax.plot``.

        Args:
            STD: Standard deviation of the sample (radial coordinate).
            r: Pearson correlation coefficient of the sample (angular
               coordinate, mapped as ``theta = arccos(r)``).
            *args: Additional positional arguments passed to ``ax.plot``
                   (e.g., marker style strings).
            **kwargs: Additional keyword arguments passed to ``ax.plot``
                      (e.g., ``label``, ``color``, ``markersize``).

        Returns:
            matplotlib Line2D artist for the plotted point.
        """
        (l,) = self.ax.plot(np.arccos(r), STD, *args, **kwargs)
        self.samplePoints.append(l)
        return l

    def add_contours(self, levels=5, **kwargs):
        """
        Overlay RMSE contour lines on the Taylor diagram.

        Computes the centred root-mean-square error (RMSE after removing the
        mean bias) on a mesh of (theta, r) values and draws contour lines
        using ``ax.contour``.  The contours radiate from the reference point.

        Args:
            levels: Number of evenly-spaced contour levels, or an explicit
                    sequence of RMSE values at which to draw contours
                    (default: 5).
            **kwargs: Additional keyword arguments forwarded to
                      ``ax.contour`` (e.g., ``colors``, ``linewidths``).

        Returns:
            matplotlib QuadContourSet returned by ``ax.contour``.
        """
        rs, ts = np.meshgrid(
            np.linspace(self.smin, self.smax),
            np.linspace(0, self.theta_max),
        )
        RMSE = np.sqrt(
            self.STD**2 + rs**2 - 2.0 * self.STD * rs * np.cos(ts)
        )
        contours = self.ax.contour(ts, rs, RMSE, levels, **kwargs)
        return contours

    def queue_offchart(self, STD, r, label='', marker='o', color='blue',
                       markersize=8, **kwargs):
        """
        Register an off-chart point for later batch drawing.

        Stores the point's statistics so that ``flush_offchart()`` can draw
        all queued points together with proportionally scaled arrows.  Using
        the queue/flush pattern ensures that arrow lengths are scaled relative
        to one another rather than being drawn independently.

        Args:
            STD: True standard deviation of the point (may exceed ``smax``).
            r: Pearson correlation coefficient of the point.
            label: Legend label for the point (default: '').
            marker: Matplotlib marker style string (default: 'o').
            color: Marker and arrow colour (default: 'blue').
            markersize: Marker size in points (default: 8).
            **kwargs: Additional keyword arguments forwarded to ``ax.plot``
                      when the marker is drawn.

        Returns:
            None
        """
        self._offchart_queue.append(dict(
            STD=STD, r=r, label=label, marker=marker, color=color,
            markersize=markersize, **kwargs
        ))

    def flush_offchart(self, base_fraction=0.82, arrow_zone=0.15,
                       min_arrow=0.03):
        """
        Draw all queued off-chart points with proportionally scaled arrows.

        Arrow length scales linearly with how far the true σ exceeds
        ``smax``, normalised so the most extreme point gets the longest
        arrow and closer points get shorter ones.  Each marker is placed
        inside the diagram boundary with an upward-pointing arrow indicating
        that the true value lies beyond the axis, and a σ label alternating
        sides to avoid overlap.  Clears the internal queue after drawing.

        Args:
            base_fraction: Radial position of the marker base as a fraction
                           of ``smax`` (default: 0.82).
            arrow_zone: Maximum arrow length as a fraction of ``smax``
                        (default: 0.15).
            min_arrow: Minimum arrow length as a fraction of ``smax``
                       (default: 0.03).

        Returns:
            None
        """
        if not self._offchart_queue:
            return

        stds = [p['STD'] for p in self._offchart_queue]
        max_excess = max(stds) - self.smax
        if max_excess <= 0:
            max_excess = 1.0  # safety

        for idx, entry in enumerate(self._offchart_queue):
            STD = entry.pop('STD')
            r = entry.pop('r')
            label = entry.pop('label', '')
            marker = entry.pop('marker', 'o')
            color = entry.pop('color', 'blue')
            markersize = entry.pop('markersize', 8)

            theta = np.arccos(np.clip(r, -1, 1))
            r_plot = self.smax * (base_fraction - idx * 0.06)

            # Proportional arrow: longest for max σ, shortest for min
            excess = STD - self.smax
            norm = max(excess / max_excess, 0.0)  # 0..1
            dr = self.smax * (min_arrow + norm * arrow_zone)

            # Marker
            (l,) = self.ax.plot(
                theta, r_plot, marker=marker, color=color,
                markersize=markersize, linestyle='', label=label,
                **entry
            )
            self.samplePoints.append(l)

            # Arrow (proportional length)
            self.ax.annotate(
                '', xy=(theta, r_plot + dr), xytext=(theta, r_plot),
                arrowprops=dict(arrowstyle='->', color=color, lw=2.0),
            )

            # σ label — alternate sides to avoid overlap
            dtheta = 0.15 if idx % 2 == 0 else -0.15
            valign = 'bottom' if idx % 2 == 0 else 'top'
            halign = 'left' if idx % 2 == 0 else 'right'
            self.ax.text(
                theta + dtheta, r_plot,
                f'σ={STD:.0f}', fontsize=8, color=color,
                ha=halign, va=valign, fontweight='bold',
            )

        self._offchart_queue.clear()

    # Keep the direct method for one-off use, but prefer queue/flush
    def add_offchart_arrow(self, STD, r, label='', marker='o', color='blue',
                           markersize=8, offset_fraction=0.92, **kwargs):
        """
        Draw a single off-chart arrow immediately (non-proportional, legacy).

        Places the marker at a fixed radial position (``offset_fraction *
        smax``) with a short upward arrow and a σ label.  Prefer the
        ``queue_offchart`` / ``flush_offchart`` workflow when plotting
        multiple off-chart sensors so that arrow lengths scale proportionally.

        Args:
            STD: True standard deviation of the point (used for the σ label
                 only; the marker is drawn inside the diagram boundary).
            r: Pearson correlation coefficient of the point.
            label: Legend label for the point (default: '').
            marker: Matplotlib marker style string (default: 'o').
            color: Marker and arrow colour (default: 'blue').
            markersize: Marker size in points (default: 8).
            offset_fraction: Radial position of the marker as a fraction of
                             ``smax`` (default: 0.92).
            **kwargs: Additional keyword arguments forwarded to ``ax.plot``.

        Returns:
            matplotlib Line2D artist for the plotted marker.
        """
        theta = np.arccos(np.clip(r, -1, 1))
        r_plot = self.smax * offset_fraction

        (l,) = self.ax.plot(
            theta, r_plot, marker=marker, color=color,
            markersize=markersize, linestyle='', label=label, **kwargs
        )
        self.samplePoints.append(l)

        dr = self.smax * 0.06
        self.ax.annotate(
            '', xy=(theta, r_plot + dr), xytext=(theta, r_plot),
            arrowprops=dict(arrowstyle='->', color=color, lw=2),
        )
        # self.ax.text(
        #     theta + 0.06, r_plot,
        #     f'σ={STD:.0f}', fontsize=8, color=color,
        #     ha='left', va='center', fontweight='bold',
        # )
        # σ label — radially below marker
        self.ax.text(
            theta, r_plot - self.smax * 0.05,
            f'σ={STD:.0f}', fontsize=8, color=color,
            ha='center', va='top', fontweight='bold',
        )
        return l


class TaylorPlotter(BasePlotter):
    """High-level interface: merged CSV → Taylor diagram figure."""

    # Colours/markers for up to 6 sensors
    COLOURS = ['#d62728', '#1f77b4', '#2ca02c', '#9467bd', '#e7298a', '#66a61e']
    MARKERS = ['o', 's', '^', 'D', 'v', 'p']

    def plot(self, ref_csv, scd_csvs, ref_name,
             title='Taylor Diagram: SCD41 vs LGR Reference',
             filename='taylor_diagram.png'):
        """
        Build a Taylor diagram comparing SCD41 sensors against a reference.

        Loads the reference and test sensor CSVs, merges them on timestamp,
        computes standard deviation and Pearson correlation for each sensor,
        then draws a ``TaylorDiagram`` with RMSE contours, per-sensor markers,
        and a legend.  Sensors whose standard deviation exceeds 95 % of the
        diagram's radial limit are rendered as off-chart arrows via the
        queue/flush mechanism.

        Args:
            ref_csv: Path to the reference (e.g., LGR) 10-minute CSV file.
            scd_csvs: Dict mapping sensor display names to their 10-minute CSV
                      paths, e.g. ``{'CO2_30M_A': Path('CO2_30M_A_10min.csv')}``.
            ref_name: Display name for the reference instrument used in the
                      legend and diagram title.
            title: Figure suptitle string
                   (default: 'Taylor Diagram: SCD41 vs LGR Reference').
            filename: Output filename saved to ``output_dir``
                      (default: 'taylor_diagram.png').

        Returns:
            matplotlib Figure object, or None if no sensor has at least 10
            overlapping timestamps with the reference.
        """
        # --- stats ---
        # ref_df = pd.read_csv(ref_csv, parse_dates=['timestamp'])
        ref_df = pd.read_csv(ref_csv, parse_dates=['timestamp'])
        ref_df['timestamp'] = pd.to_datetime(ref_df['timestamp'], format='mixed')

        ref_col = self._detect_co2_column(ref_df)
        ref_df = self._apply_qc_filter(ref_df, ref_col)
        ref_std = float(ref_df[ref_col].std(ddof=1))

        stats = {}
        for name, csv_path in scd_csvs.items():
            # test_df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            
            test_df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            test_df['timestamp'] = pd.to_datetime(test_df['timestamp'], format='mixed')

            test_col = self._detect_co2_column(test_df)

            test_df = self._apply_qc_filter(test_df, test_col)

            self.logger.debug("%s ref dtype=%s test dtype=%s",
                              name, 
                              ref_df['timestamp'].dtype, 
                              test_df['timestamp'].dtype)
            
            merged = pd.merge(
                ref_df[['timestamp', ref_col]],
                test_df[['timestamp', test_col]],
                on='timestamp', how='inner',
            ).dropna()
            if len(merged) < 10:
                self.logger.warning("%s: <10 overlapping points, skipping", name)
                continue
            r_vals, t_vals = merged[ref_col].values, merged[test_col].values
            stats[name] = {
                'std':  np.std(t_vals, ddof=1),
                'corr': np.corrcoef(r_vals, t_vals)[0, 1],
            }

        if not stats:
            self.logger.warning("No valid sensor pairs for Taylor diagram")
            return None

        # --- diagram (temporarily override style) ---
        import matplotlib
        prev_style = matplotlib.rcParams.copy()
        plt.style.use('default')
        plt.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'font.size': 11,
            'pdf.fonttype': 42,
        })

        try:
            fig = plt.figure(figsize=(10, 7))
            dia = TaylorDiagram.from_stats(
                ref_std,
                correlations=[s['corr'] for s in stats.values()],
                fig=fig, rect=111,
                label=f'{ref_name} (σ={ref_std:.1f} ppm)',
            )
            plt.clabel(dia.add_contours(colors='0.5'), inline=True, fontsize=10)

            for i, (name, s) in enumerate(stats.items()):
                # Human-readable legend label
                display = name.replace("CO2_SCT1_", "SCD41 ").replace("CO2_30M_", "SCD41 ").replace("2M", "2m")
                if "30M" in name.upper():
                    display += " (30m)"
                kw = dict(
                    label=f"{display} (r={s['corr']:.2f}, σ={s['std']:.0f})",
                    marker=self.MARKERS[i % len(self.MARKERS)],
                    color=self.COLOURS[i % len(self.COLOURS)],
                    markersize=10,
                    markeredgecolor='black',
                    markeredgewidth=1.2,
                )
                if s['std'] > dia.smax * 0.95:
                    dia.queue_offchart(s['std'], s['corr'], **kw)
                else:
                    dia.add_sample(s['std'], s['corr'], linestyle='None', **kw)

            dia.flush_offchart()

            fig.legend(
                dia.samplePoints,
                [p.get_label() for p in dia.samplePoints],
                numpoints=1, loc='upper right',
                bbox_to_anchor=(0.98, 0.95),
                frameon=True, framealpha=0.9, fontsize=10,
            )
            fig.suptitle(title, fontweight='bold', fontsize=13)
            plt.tight_layout()
            self._save_figure(fig, filename)
        finally:
            matplotlib.rcParams.update(prev_style)

        return fig

if __name__ == "__main__":
    refstd = 1.0

    fig = plt.figure(figsize=(10, 7))
    dia = TaylorDiagram.from_stats(
        refstd,
        correlations=[0.95, 0.85, -0.3],
        fig=fig, rect=111,
        label='Reference (σ=1.0)',
    )
    plt.clabel(dia.add_contours(colors='0.5'), inline=True, fontsize=10)

    dia.add_sample(0.8, 0.95, label='Good model', marker='o',
                   color='green', markersize=10, linestyle='None')
    dia.add_sample(1.2, 0.85, label='OK model', marker='s',
                   color='blue', markersize=10, linestyle='None')

    # Off-chart example with negative correlation
    dia.queue_offchart(2.5, -0.3, label='Poor model (σ=2.5)',
                       marker='^', color='red', markersize=10)
    dia.flush_offchart()

    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
               numpoints=1, loc='upper right', frameon=True)
    fig.suptitle('Example Taylor Diagram', fontweight='bold')
    plt.tight_layout()
    plt.show()