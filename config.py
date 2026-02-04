"""
Configuration settings for IP SLA Monitor.

Centralizes all configurable paths and constants.
"""

from pathlib import Path

# Base directory (module root)
BASE_DIR = Path(__file__).parent.resolve()

# Input directory for raw Cisco IP SLA output files
INPUT_DIR = BASE_DIR / "input"

# Output Excel file
OUTPUT_FILE = BASE_DIR / "Ip_SLA_measurements.xlsx"

# Excel sheet names
DATA_SHEET = "IP_SLA_Data"
CHART_SHEET_PREFIX = "Chart_"

# Predefined chart favorites
CHART_FAVORITES = {
    "RTT_Avg_Max": {
        "title": "RTT Average/Max Over Time",
        "y_columns": ["RTT_Avg_ms", "RTT_Max_ms"],
        "y_label": "RTT (ms)"
    },
    "Packet_Loss": {
        "title": "Packet Loss Per Interval",
        "y_columns": ["Loss_SD", "Loss_DS", "Packet_Late_Arrival", "TailDrop"],
        "y_label": "Packet Count"
    },
    "Jitter": {
        "title": "Jitter Over Time",
        "y_columns": ["Jitter_SD_Avg_ms", "Jitter_SD_Max_ms", "Jitter_DS_Avg_ms", "Jitter_DS_Max_ms"],
        "y_label": "Jitter (ms)"
    },
    "MOS_Score": {
        "title": "MOS Score Over Time",
        "y_columns": ["MinMOS", "MaxMOS"],
        "y_label": "MOS Score"
    },
    "RTT_Threshold": {
        "title": "RTT Over Threshold",
        "y_columns": ["RTT_Over_Threshold_Count", "RTT_Over_Threshold_Pct"],
        "y_label": "Count / Percentage"
    }
}

# Column order for Excel output (matches CSV format)
COLUMNS = [
    "StartTime",
    "MinMOS",
    "MaxMOS", 
    "MinICPIF",
    "MaxICPIF",
    "NumRTT",
    "RTT_Min_ms",
    "RTT_Avg_ms",
    "RTT_Max_ms",
    "RTT_Over_Threshold_Count",
    "RTT_Over_Threshold_Pct",
    "Num_OneWay_Samples",
    "Jitter_SD_Avg_ms",
    "Jitter_SD_Max_ms",
    "Jitter_DS_Avg_ms",
    "Jitter_DS_Max_ms",
    "Loss_SD",
    "Loss_DS",
    "Packet_Late_Arrival",
    "OutOfSeq",
    "TailDrop",
    "Successes",
    "Failures"
]

# Logging configuration
LOG_FILE = BASE_DIR / "ip_sla_monitor.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
