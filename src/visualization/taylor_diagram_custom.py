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


class TaylorDiagram:
    """Taylor diagram: plot model standard deviation and correlation to reference
    
    Based on the excellent implementation pattern but simplified and modernized.
    """
    
    def __init__(self, refstd: float, fig=None, rect=111, label='_'):
        """
        Set up Taylor diagram axes
        
        Args:
            refstd: Reference standard deviation (the "truth")
            fig: Input Figure or None (creates new figure)
            rect: Subplot definition (like plt.subplot(rect))
            label: Reference label
        """
        
        if fig is None:
            fig = plt.figure(figsize=(10, 10))
        
        # Transform for polar plot
        tr = PolarAxes.PolarTransform()
        
        # Correlation labels (angular axis)
        rlocs = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])
        tlocs = np.arccos(rlocs)  # Convert to angles
        gl1 = transforms.FixedLocator(tlocs)  # Positions
        tf1 = transforms.DictFormatter(dict(zip(tlocs, map(str, rlocs))))
        
        # Standard deviation axis (radial)
        self.smin = 0
        self.smax = 1.5 * refstd  # Can be updated later
        
        # Create polar axes
        ax = fig.add_subplot(rect, projection='polar')
        ax.set_theta_direction(-1)  # Clockwise
        ax.set_theta_offset(np.pi / 2)  # Put 0 at top
        
        # Only show right half of polar plot
        ax.set_thetamin(0)
        ax.set_thetamax(90)
        
        # Set up correlation labels
        ax.xaxis.set_major_locator(gl1)
        ax.xaxis.set_major_formatter(tf1)
        ax.set_xlabel('Correlation', fontweight='bold')
        
        # Set up radial (std dev) axis
        ax.set_ylim(0, self.smax)
        ax.set_ylabel('Standard Deviation', fontweight='bold')
        
        # Grid
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Reference point at (1, 0) - perfect correlation, same std dev
        self.refstd = refstd
        self.ax = ax
        self.fig = fig
        
        # Store for later plotting
        self.sample_points = []
        
    def add_sample(self, stddev: float, corrcoef: float, label: str = '',
                   marker: str = 'o', color: str = 'blue', size: int = 8,
                   **kwargs):
        """
        Add a sample (test sensor/model) to the diagram
        
        Args:
            stddev: Standard deviation of the sample
            corrcoef: Correlation coefficient with reference
            label: Label for legend
            marker: Marker style
            color: Marker color
            size: Marker size
            **kwargs: Additional matplotlib scatter kwargs
        """
        
        # Convert to polar coordinates
        theta = np.arccos(corrcoef)  # Angle from correlation
        r = stddev  # Radius from std dev
        
        # Plot
        l = self.ax.plot(theta, r, marker=marker, color=color, 
                        markersize=size, label=label, linestyle='',
                        **kwargs)
        
        self.sample_points.append((stddev, corrcoef, label))
        
        # Update axis limits if needed
        if stddev > self.smax:
            self.smax = stddev * 1.1
            self.ax.set_ylim(0, self.smax)
        
        return l
    
    def add_reference(self, label: str = 'Reference', marker: str = '*',
                     color: str = 'red', size: int = 12):
        """Add reference point at (refstd, 1.0)"""
        self.ax.plot(0, self.refstd, marker=marker, color=color,
                    markersize=size, label=label, linestyle='',
                    markeredgewidth=1.5, markeredgecolor='black')
    
    def add_contours(self, levels: Optional[List[float]] = None,
                     colors: str = 'gray', linewidths: float = 1.0):
        """
        Add RMSD contours
        
        The centered RMS difference is related to standard deviation and
        correlation by the law of cosines:
        RMSD² = σ_model² + σ_ref² - 2*σ_model*σ_ref*r
        """
        
        if levels is None:
            # Auto-generate sensible levels
            levels = np.linspace(0, self.smax, 6)[1:]  # Skip 0
        
        # Generate contours
        rs, ts = np.meshgrid(
            np.linspace(0, self.smax, 100),
            np.linspace(0, np.pi/2, 100)
        )
        
        # Calculate RMSD for each point
        rms = np.sqrt(
            self.refstd**2 + rs**2 - 
            2 * self.refstd * rs * np.cos(ts)
        )
        
        # Draw contours
        contours = self.ax.contour(
            ts, rs, rms, levels=levels,
            colors=colors, linewidths=linewidths,
            linestyles='dotted', alpha=0.6
        )
        
        # Label contours
        self.ax.clabel(contours, inline=True, fontsize=9, fmt='%.1f')
        
        return contours
    
    def add_grid(self, which: str = 'both', **kwargs):
        """Customize grid"""
        self.ax.grid(which=which, **kwargs)
    
    def set_title(self, title: str, **kwargs):
        """Set plot title"""
        self.ax.set_title(title, **kwargs)
    
    def add_legend(self, loc: str = 'upper right', **kwargs):
        """Add legend"""
        return self.ax.legend(loc=loc, **kwargs)


class TaylorPlotter:
    """High-level interface for creating Taylor diagrams from sensor data"""
    
    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: Where to save plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _detect_co2_column(self, df: pd.DataFrame) -> str:
        """Detect CO2 column name"""
        possible_cols = [
            'CO2_dry_mean', 'co2_dry_mean', 'CO2_dry', 'co2_dry',
            'co2_mean', 'co2', 'CO2'
        ]
        
        for col in possible_cols:
            if col in df.columns:
                return col
        
        raise ValueError(f"No CO2 column found. Available: {list(df.columns)}")
    
    def calculate_statistics(self, ref_csv: Path, test_csv: Path) -> Tuple[float, float, float]:
        """
        Calculate Taylor statistics for a test sensor vs reference
        
        Returns:
            (std_dev, correlation, centered_rmsd)
        """
        # Load data
        ref = pd.read_csv(ref_csv, parse_dates=['timestamp'])
        test = pd.read_csv(test_csv, parse_dates=['timestamp'])
        
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
            raise ValueError("No overlapping data points")
        
        # Calculate statistics
        ref_vals = merged[ref_col].values
        test_vals = merged[test_col].values
        
        # Standard deviation of test
        test_std = np.std(test_vals, ddof=1)
        
        # Correlation
        corr = np.corrcoef(ref_vals, test_vals)[0, 1]
        
        # Centered RMSD (remove mean bias first)
        ref_anom = ref_vals - np.mean(ref_vals)
        test_anom = test_vals - np.mean(test_vals)
        crmsd = np.sqrt(np.mean((test_anom - ref_anom)**2))
        
        return test_std, corr, crmsd
    
    def plot_from_config(
        self,
        config,
        test_sensor_ids: Optional[List[str]] = None,
        title: str = "Taylor Diagram: Multi-Sensor CO2 Comparison",
        add_contours: bool = True,
        save: bool = True,
        filename: str = "taylor_diagram.png"
    ) -> plt.Figure:
        """
        Create Taylor diagram from config
        
        Args:
            config: PipelineConfig object
            test_sensor_ids: List of sensor names/IDs to include (None = all)
            title: Plot title
            add_contours: Add RMSD contours
            save: Save to file
            filename: Output filename
        """
        
        # Get paths from config
        output_dir = Path(config.output_dir)
        
        # Find reference sensor
        ref_sensor = next(s for s in config.sensors if 'lgr' in s.sensor_type.lower())
        ref_csv = output_dir / f"{ref_sensor.name}_10min.csv"
        
        # Calculate reference std dev
        ref_data = pd.read_csv(ref_csv, parse_dates=['timestamp'])
        ref_col = self._detect_co2_column(ref_data)
        ref_std = np.std(ref_data[ref_col].dropna(), ddof=1)
        
        print(f"Reference std dev: {ref_std:.2f} ppm")
        
        # Create Taylor diagram
        dia = TaylorDiagram(ref_std, label=ref_sensor.name)
        dia.add_reference(label=ref_sensor.name)
        
        # Get test sensors
        test_sensors = [s for s in config.sensors if 'lgr' not in s.sensor_type.lower()]
        
        if test_sensor_ids is not None:
            test_sensors = [s for s in test_sensors 
                          if s.name in test_sensor_ids or s.sensor_id in test_sensor_ids]
        
        # Colors and markers for test sensors
        colors = ['#1b9e77', '#d95f02', '#7570b3', '#e7298a', '#66a61e', '#e6ab02']
        markers = ['o', 's', '^', 'd', 'v', 'p']
        
        # Add each test sensor
        for i, sensor in enumerate(test_sensors):
            test_csv = output_dir / f"{sensor.name}_10min.csv"
            
            try:
                std, corr, crmsd = self.calculate_statistics(ref_csv, test_csv)
                
                print(f"{sensor.name}: std={std:.2f}, r={corr:.3f}, CRMSD={crmsd:.2f}")
                
                dia.add_sample(
                    std, corr, label=sensor.name,
                    marker=markers[i % len(markers)],
                    color=colors[i % len(colors)],
                    size=10,
                    markeredgewidth=1.5,
                    markeredgecolor='black',
                    alpha=0.8
                )
                
            except Exception as e:
                print(f"Warning: Could not process {sensor.name}: {e}")
        
        # Add RMSD contours
        if add_contours:
            dia.add_contours()
        
        # Styling
        dia.set_title(title, fontsize=14, fontweight='bold', pad=20)
        dia.add_legend(loc='upper left', frameon=True, framealpha=0.9)
        
        plt.tight_layout()
        
        # Save
        if save:
            filepath = self.output_dir / filename
            dia.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            print(f"Saved: {filepath}")
        
        return dia.fig


# Example usage
if __name__ == "__main__":
    # Create simple example
    refstd = 1.0  # Reference has std dev of 1.0
    
    dia = TaylorDiagram(refstd)
    dia.add_reference(label='Reference')
    
    # Add some test points
    dia.add_sample(0.8, 0.95, label='Good Model', marker='o', color='green')
    dia.add_sample(1.2, 0.85, label='OK Model', marker='s', color='blue')
    dia.add_sample(1.5, 0.60, label='Poor Model', marker='^', color='red')
    
    dia.add_contours()
    dia.set_title('Example Taylor Diagram')
    dia.add_legend()
    
    plt.show()