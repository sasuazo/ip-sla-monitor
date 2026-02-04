"""
IP SLA Monitor - Cisco IP SLA measurement ingestion and visualization tool.

A Python module for:
- Parsing Cisco 'show ip sla statistics aggregated' output
- Storing measurements in Excel with deduplication
- Generating charts with predefined favorites

Usage:
    python -m ip_sla_monitor <command>
    
Commands:
    ingest <file>    Ingest a raw data file
    ingest-all       Ingest all files in input/
    charts           Launch chart generation GUI
    charts-cli       Generate charts from CLI
    status           Show data status
"""

__version__ = "1.0.0"
__author__ = "IP SLA Monitor"

from .parser import IPSLAParser, IPSLARecord
from .excel_handler import ExcelHandler
from .chart_manager import ChartManager
from .config import INPUT_DIR, OUTPUT_FILE, CHART_FAVORITES

__all__ = [
    'IPSLAParser',
    'IPSLARecord', 
    'ExcelHandler',
    'ChartManager',
    'INPUT_DIR',
    'OUTPUT_FILE',
    'CHART_FAVORITES',
]
