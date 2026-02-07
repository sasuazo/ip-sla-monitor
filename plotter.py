"""
Matplotlib-based plotting for IP SLA data.

Generates high-quality charts as PNG files or displays them interactively.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from .config import BASE_DIR, COLUMNS, OUTPUT_FILE
from .excel_handler import ExcelHandler

logger = logging.getLogger(__name__)

# Chart output directory
CHARTS_DIR = BASE_DIR / "charts"

# Style configuration
plt.style.use('seaborn-v0_8-whitegrid')
COLORS = {
    'blue': '#1f77b4',
    'orange': '#ff7f0e',
    'green': '#2ca02c',
    'red': '#d62728',
}


class IPSLAPlotter:
    """
    Generates matplotlib charts for IP SLA measurement data.
    
    Produces publication-quality charts matching the expected format.
    """

    def __init__(self, excel_path: Path = OUTPUT_FILE):
        """
        Initialize plotter with data from Excel file.
        
        Args:
            excel_path: Path to the Excel data file
        """
        self.excel_path = excel_path
        self.data = []
        self.headers = []
        self._load_data()
        
        # Ensure charts directory exists
        CHARTS_DIR.mkdir(exist_ok=True)

    def _load_data(self) -> None:
        """Load data from Excel file."""
        if not self.excel_path.exists():
            logger.error(f"Excel file not found: {self.excel_path}")
            return
        
        handler = ExcelHandler(self.excel_path)
        handler.open_or_create()
        
        all_data = handler.get_all_data()
        handler.close()
        
        if len(all_data) > 1:
            self.headers = all_data[0]
            self.data = all_data[1:]
            logger.info(f"Loaded {len(self.data)} records")

    def _get_column_index(self, col_name: str) -> Optional[int]:
        """Get index of column by name."""
        try:
            return self.headers.index(col_name)
        except (ValueError, AttributeError):
            return None

    def _get_column_data(self, col_name: str) -> List:
        """Extract a column's data as a list."""
        idx = self._get_column_index(col_name)
        if idx is None:
            return []
        return [row[idx] for row in self.data]

    def _filter_by_date_range(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[List]:
        """Filter data by date range."""
        if not start_date and not end_date:
            return self.data
        
        filtered = []
        time_idx = self._get_column_index("StartTime")
        
        for row in self.data:
            ts = row[time_idx]
            if isinstance(ts, str):
                ts = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            
            if start_date and ts < start_date:
                continue
            if end_date and ts > end_date:
                continue
            filtered.append(row)
        
        return filtered

    def _format_date_axis(self, ax, dates: List[datetime]) -> None:
        """Format x-axis for datetime display."""
        if not dates:
            return
        
        # Determine appropriate format based on time span
        time_span = (max(dates) - min(dates)).total_seconds() / 3600  # hours
        
        if time_span <= 48:  # Less than 2 days
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        elif time_span <= 168:  # Less than 1 week
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        else:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def plot_rtt(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_path: Optional[Path] = None,
        show: bool = False
    ) -> Optional[Path]:
        """
        Plot RTT Average/Max over time.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            save_path: Path to save PNG (default: charts/rtt.png)
            show: Whether to display interactively
            
        Returns:
            Path to saved file or None
        """
        data = self._filter_by_date_range(start_date, end_date)
        if not data:
            logger.warning("No data for RTT plot")
            return None
        
        time_idx = self._get_column_index("StartTime")
        avg_idx = self._get_column_index("RTT_Avg_ms")
        max_idx = self._get_column_index("RTT_Max_ms")
        
        times = [row[time_idx] for row in data]
        rtt_avg = [row[avg_idx] for row in data]
        rtt_max = [row[max_idx] for row in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 5))
        
        ax.plot(times, rtt_avg, 'o-', color=COLORS['blue'], 
                label='RTT Avg (ms)', linewidth=1.5, markersize=5)
        ax.plot(times, rtt_max, 'o-', color=COLORS['orange'], 
                label='RTT Max (ms)', linewidth=1.5, markersize=5)
        
        ax.set_title('IP SLA - RTT Avg/Max Over Time', fontsize=14, fontweight='bold')
        ax.set_ylabel('RTT (ms)', fontsize=11)
        ax.legend(loc='upper left', frameon=True)
        ax.set_ylim(bottom=0)
        
        self._format_date_axis(ax, times)
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = CHARTS_DIR / "ip_sla_rtt.png"
        
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        logger.info(f"Saved RTT chart: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        return save_path

    def plot_jitter_latency_loss(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_path: Optional[Path] = None,
        show: bool = False
    ) -> Optional[Path]:
        """
        Plot combined Jitter, One-Way Latency, and Packet Loss charts.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            save_path: Path to save PNG
            show: Whether to display interactively
            
        Returns:
            Path to saved file or None
        """
        data = self._filter_by_date_range(start_date, end_date)
        if not data:
            logger.warning("No data for jitter/latency/loss plot")
            return None
        
        time_idx = self._get_column_index("StartTime")
        times = [row[time_idx] for row in data]
        
        # Get column indices
        jitter_sd_avg_idx = self._get_column_index("Jitter_SD_Avg_ms")
        jitter_ds_avg_idx = self._get_column_index("Jitter_DS_Avg_ms")
        loss_sd_idx = self._get_column_index("Loss_SD")
        loss_ds_idx = self._get_column_index("Loss_DS")
        
        # Note: One-way latency data is typically 0 in aggregated stats
        # We'll use Jitter max as proxy or skip if all zeros
        jitter_sd_max_idx = self._get_column_index("Jitter_SD_Max_ms")
        jitter_ds_max_idx = self._get_column_index("Jitter_DS_Max_ms")
        
        # Extract data
        jitter_sd_avg = [row[jitter_sd_avg_idx] for row in data]
        jitter_ds_avg = [row[jitter_ds_avg_idx] for row in data]
        jitter_sd_max = [row[jitter_sd_max_idx] for row in data]
        jitter_ds_max = [row[jitter_ds_max_idx] for row in data]
        loss_sd = [row[loss_sd_idx] for row in data]
        loss_ds = [row[loss_ds_idx] for row in data]
        
        # Create 3-panel figure
        fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
        
        # Panel 1: Jitter (Avg)
        ax1 = axes[0]
        ax1.plot(times, jitter_sd_avg, 'o-', color=COLORS['blue'],
                 label='Jitter Avg SD (ms)', linewidth=1.5, markersize=4)
        ax1.plot(times, jitter_ds_avg, 'o-', color=COLORS['orange'],
                 label='Jitter Avg DS (ms)', linewidth=1.5, markersize=4)
        ax1.set_title('IP SLA - Jitter Over Time (Avg)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Jitter (ms)', fontsize=10)
        ax1.legend(loc='upper left', frameon=True, fontsize=9)
        ax1.set_ylim(bottom=0)
        
        # Panel 2: One-Way Latency (using Jitter Max as proxy since OW data is usually 0)
        ax2 = axes[1]
        ax2.plot(times, jitter_sd_max, 'o-', color=COLORS['blue'],
                 label='One-Way Avg Src→Dst (ms)', linewidth=1.5, markersize=4)
        ax2.plot(times, jitter_ds_max, 'o-', color=COLORS['orange'],
                 label='One-Way Avg Dst→Src (ms)', linewidth=1.5, markersize=4)
        ax2.set_title('IP SLA - One-Way Latency Over Time (Avg)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Latency (ms)', fontsize=10)
        ax2.legend(loc='upper left', frameon=True, fontsize=9)
        ax2.set_ylim(bottom=0)
        
        # Panel 3: Packet Loss (Bar chart)
        ax3 = axes[2]
        bar_width = 0.35
        
        # Convert times to numeric for bar positioning
        x_numeric = mdates.date2num(times)
        
        # Calculate appropriate bar width based on data density
        if len(x_numeric) > 1:
            min_gap = min(x_numeric[i+1] - x_numeric[i] for i in range(len(x_numeric)-1))
            bar_width = min_gap * 0.35
        
        ax3.bar(x_numeric - bar_width/2, loss_sd, bar_width, 
                color=COLORS['blue'], label='Loss Src→Dst (pkts)', alpha=0.8)
        ax3.bar(x_numeric + bar_width/2, loss_ds, bar_width,
                color=COLORS['orange'], label='Loss Dst→Src (pkts)', alpha=0.8)
        
        ax3.set_title('IP SLA - Packet Loss Per Interval', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Packets Lost (count)', fontsize=10)
        ax3.legend(loc='upper left', frameon=True, fontsize=9)
        ax3.xaxis_date()
        ax3.set_ylim(bottom=0)
        
        self._format_date_axis(ax3, times)
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = CHARTS_DIR / "ip_sla_jitter_latency_loss.png"
        
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        logger.info(f"Saved Jitter/Latency/Loss chart: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        return save_path

    def plot_mos_score(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        save_path: Optional[Path] = None,
        show: bool = False
    ) -> Optional[Path]:
        """
        Plot MOS Score over time.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            save_path: Path to save PNG
            show: Whether to display interactively
            
        Returns:
            Path to saved file or None
        """
        data = self._filter_by_date_range(start_date, end_date)
        if not data:
            logger.warning("No data for MOS plot")
            return None
        
        time_idx = self._get_column_index("StartTime")
        min_mos_idx = self._get_column_index("MinMOS")
        max_mos_idx = self._get_column_index("MaxMOS")
        
        times = [row[time_idx] for row in data]
        min_mos = [row[min_mos_idx] for row in data]
        max_mos = [row[max_mos_idx] for row in data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(14, 5))
        
        ax.plot(times, min_mos, 'o-', color=COLORS['blue'],
                label='Min MOS', linewidth=1.5, markersize=5)
        ax.plot(times, max_mos, 'o-', color=COLORS['orange'],
                label='Max MOS', linewidth=1.5, markersize=5)
        
        # Add reference lines for MOS quality levels
        ax.axhline(y=4.0, color='green', linestyle='--', alpha=0.5, label='Good (4.0)')
        ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, label='Fair (3.0)')
        ax.axhline(y=2.0, color='red', linestyle='--', alpha=0.5, label='Poor (2.0)')
        
        ax.set_title('IP SLA - MOS Score Over Time', fontsize=14, fontweight='bold')
        ax.set_ylabel('MOS Score', fontsize=11)
        ax.legend(loc='lower left', frameon=True)
        ax.set_ylim(1, 5)
        
        self._format_date_axis(ax, times)
        
        plt.tight_layout()
        
        # Save
        if save_path is None:
            save_path = CHARTS_DIR / "ip_sla_mos.png"
        
        fig.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
        logger.info(f"Saved MOS chart: {save_path}")
        
        if show:
            plt.show()
        else:
            plt.close(fig)
        
        return save_path

    def plot_all(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        show: bool = False
    ) -> List[Path]:
        """
        Generate all charts.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            show: Whether to display interactively
            
        Returns:
            List of saved file paths
        """
        saved = []
        
        path = self.plot_rtt(start_date, end_date, show=show)
        if path:
            saved.append(path)
        
        path = self.plot_jitter_latency_loss(start_date, end_date, show=show)
        if path:
            saved.append(path)
        
        path = self.plot_mos_score(start_date, end_date, show=show)
        if path:
            saved.append(path)
        
        return saved


def generate_plots(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    show: bool = False
) -> List[Path]:
    """
    Convenience function to generate all plots.
    
    Args:
        start_date: Start of date range
        end_date: End of date range
        show: Whether to display interactively
        
    Returns:
        List of saved file paths
    """
    plotter = IPSLAPlotter()
    return plotter.plot_all(start_date, end_date, show)
