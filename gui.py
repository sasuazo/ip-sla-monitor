"""
GUI for IP SLA chart generation.

Provides a simple tkinter interface for selecting time ranges
and generating favorite charts.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging

from .config import OUTPUT_FILE
from .excel_handler import ExcelHandler
from .plotter import IPSLAPlotter, CHARTS_DIR

logger = logging.getLogger(__name__)


class DateTimeEntry(ttk.Frame):
    """Custom widget for datetime input."""
    
    def __init__(self, parent, label: str, **kwargs):
        super().__init__(parent, **kwargs)
        
        ttk.Label(self, text=label, width=12).pack(side=tk.LEFT, padx=2)
        
        # Date entry
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(self, textvariable=self.date_var, width=12)
        self.date_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self, text="@").pack(side=tk.LEFT)
        
        # Time entry
        self.time_var = tk.StringVar(value="00:00")
        self.time_entry = ttk.Entry(self, textvariable=self.time_var, width=8)
        self.time_entry.pack(side=tk.LEFT, padx=2)
        
        # Placeholder hint
        self.date_entry.insert(0, "YYYY-MM-DD")
        self.date_entry.bind('<FocusIn>', self._clear_placeholder)
    
    def _clear_placeholder(self, event):
        if self.date_var.get() == "YYYY-MM-DD":
            self.date_entry.delete(0, tk.END)
    
    def get_datetime(self) -> Optional[datetime]:
        """Get the datetime value or None if empty/invalid."""
        date_str = self.date_var.get().strip()
        time_str = self.time_var.get().strip()
        
        if not date_str or date_str == "YYYY-MM-DD":
            return None
        
        try:
            dt_str = f"{date_str} {time_str}"
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return None
    
    def set_datetime(self, dt: Optional[datetime]) -> None:
        """Set the datetime value."""
        if dt:
            self.date_var.set(dt.strftime("%Y-%m-%d"))
            self.time_var.set(dt.strftime("%H:%M"))
        else:
            self.date_var.set("")
            self.time_var.set("00:00")


class ChartGeneratorGUI:
    """
    Main GUI window for chart generation.
    
    Allows users to select favorite charts and time ranges,
    then generates the charts in the Excel workbook.
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("IP SLA Chart Generator")
        self.root.geometry("500x580")
        self.root.resizable(True, True)
        self.root.minsize(500, 580)
        
        # Data range info
        self.data_start: Optional[datetime] = None
        self.data_end: Optional[datetime] = None
        
        self._create_widgets()
        self._load_data_info()
    
    def _create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # File info section
        info_frame = ttk.LabelFrame(main_frame, text="Data File", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_label = ttk.Label(info_frame, text=f"File: {OUTPUT_FILE.name}")
        self.file_label.pack(anchor=tk.W)
        
        self.range_label = ttk.Label(info_frame, text="Data range: Loading...")
        self.range_label.pack(anchor=tk.W)
        
        self.records_label = ttk.Label(info_frame, text="Records: Loading...")
        self.records_label.pack(anchor=tk.W)
        
        ttk.Button(info_frame, text="Refresh", command=self._load_data_info).pack(anchor=tk.E)
        
        # Time range section
        time_frame = ttk.LabelFrame(main_frame, text="Time Range", padding="5")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_entry = DateTimeEntry(time_frame, "Start:")
        self.start_entry.pack(fill=tk.X, pady=2)
        
        self.end_entry = DateTimeEntry(time_frame, "End:")
        self.end_entry.pack(fill=tk.X, pady=2)
        
        # Quick range buttons
        quick_frame = ttk.Frame(time_frame)
        quick_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(quick_frame, text="Last 24h", command=lambda: self._set_quick_range(hours=24)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Last 7d", command=lambda: self._set_quick_range(days=7)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Last 30d", command=lambda: self._set_quick_range(days=30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="All Data", command=self._set_all_range).pack(side=tk.LEFT, padx=2)
        
        # Chart selection section
        chart_frame = ttk.LabelFrame(main_frame, text="Select Charts", padding="5")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Checkboxes for matplotlib charts
        self.chart_vars = {}
        
        chart_options = [
            ("RTT_Avg_Max", "RTT Average/Max Over Time"),
            ("Jitter_Latency_Loss", "Jitter, Latency & Packet Loss"),
            ("MOS_Score", "MOS Score Over Time"),
        ]
        
        for name, title in chart_options:
            var = tk.BooleanVar(value=True)
            self.chart_vars[name] = var
            cb = ttk.Checkbutton(chart_frame, text=title, variable=var)
            cb.pack(anchor=tk.W, pady=1)
        
        # Select all/none buttons
        sel_frame = ttk.Frame(chart_frame)
        sel_frame.pack(fill=tk.X, pady=5)
        ttk.Button(sel_frame, text="Select All", command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(sel_frame, text="Select None", command=self._select_none).pack(side=tk.LEFT, padx=2)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Generate Charts", command=self._generate_charts).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Charts Folder", command=lambda: self._open_folder(CHARTS_DIR)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Open Excel", command=self._open_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
    
    def _load_data_info(self) -> None:
        """Load and display data file information."""
        try:
            if not OUTPUT_FILE.exists():
                self.range_label.config(text="Data range: No file found")
                self.records_label.config(text="Records: 0")
                return
            
            handler = ExcelHandler()
            handler.open_or_create()
            
            self.data_start, self.data_end = handler.get_data_range()
            timestamps = handler.get_existing_timestamps()
            
            handler.close()
            
            if self.data_start and self.data_end:
                self.range_label.config(
                    text=f"Data range: {self.data_start.strftime('%Y-%m-%d %H:%M')} to "
                         f"{self.data_end.strftime('%Y-%m-%d %H:%M')}"
                )
                # Set default range to all data
                self.start_entry.set_datetime(self.data_start)
                self.end_entry.set_datetime(self.data_end)
            else:
                self.range_label.config(text="Data range: No data")
            
            self.records_label.config(text=f"Records: {len(timestamps)}")
            
        except Exception as e:
            logger.error(f"Error loading data info: {e}")
            self.range_label.config(text=f"Error: {e}")
    
    def _set_quick_range(self, hours: int = 0, days: int = 0) -> None:
        """Set a quick time range relative to data end."""
        if self.data_end:
            end = self.data_end
            start = end - timedelta(hours=hours, days=days)
            self.start_entry.set_datetime(start)
            self.end_entry.set_datetime(end)
    
    def _set_all_range(self) -> None:
        """Set range to all available data."""
        self.start_entry.set_datetime(self.data_start)
        self.end_entry.set_datetime(self.data_end)
    
    def _select_all(self) -> None:
        """Select all chart checkboxes."""
        for var in self.chart_vars.values():
            var.set(True)
    
    def _select_none(self) -> None:
        """Deselect all chart checkboxes."""
        for var in self.chart_vars.values():
            var.set(False)
    
    def _generate_charts(self) -> None:
        """Generate selected charts using matplotlib."""
        # Get selected charts
        selected = [name for name, var in self.chart_vars.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("No Selection", "Please select at least one chart type.")
            return
        
        # Get time range
        start_date = self.start_entry.get_datetime()
        end_date = self.end_entry.get_datetime()
        
        try:
            plotter = IPSLAPlotter()
            created = []
            
            # Map checkbox names to plotter methods
            if "RTT_Avg_Max" in selected:
                path = plotter.plot_rtt(start_date, end_date)
                if path:
                    created.append(path)
            
            if "Jitter_Latency_Loss" in selected:
                path = plotter.plot_jitter_latency_loss(start_date, end_date)
                if path:
                    created.append(path)
            
            if "MOS_Score" in selected:
                path = plotter.plot_mos_score(start_date, end_date)
                if path:
                    created.append(path)
            
            if created:
                messagebox.showinfo(
                    "Success",
                    f"Created {len(created)} chart(s) in:\n{CHARTS_DIR}\n\n" + 
                    "\n".join(f"• {p.name}" for p in created)
                )
                # Open charts folder
                self._open_folder(CHARTS_DIR)
            else:
                messagebox.showwarning("No Charts", "No charts were created. Check data range.")
                
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            messagebox.showerror("Error", f"Failed to generate charts:\n{e}")
    
    def _open_folder(self, folder_path) -> None:
        """Open a folder in the file browser."""
        import subprocess
        import sys
        
        folder_path.mkdir(exist_ok=True)
        
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(folder_path)])
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['explorer', str(folder_path)])
            else:  # Linux
                subprocess.run(['xdg-open', str(folder_path)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")
    
    def _open_excel(self) -> None:
        """Open the Excel file in default application."""
        import subprocess
        import sys
        
        if not OUTPUT_FILE.exists():
            messagebox.showwarning("File Not Found", f"Excel file not found:\n{OUTPUT_FILE}")
            return
        
        try:
            if sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(OUTPUT_FILE)])
            elif sys.platform == 'win32':  # Windows
                subprocess.run(['start', '', str(OUTPUT_FILE)], shell=True)
            else:  # Linux
                subprocess.run(['xdg-open', str(OUTPUT_FILE)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")
    
    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()


def show_chart_gui() -> None:
    """Launch the chart generator GUI."""
    app = ChartGeneratorGUI()
    app.run()
