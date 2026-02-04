#!/usr/bin/env python3
"""
IP SLA Monitor - Main entry point.

A tool for ingesting Cisco IP SLA measurements, storing them in Excel,
and generating charts for analysis.

Usage:
    python -m ip_sla_monitor ingest <file>     # Ingest a raw data file
    python -m ip_sla_monitor ingest-all        # Ingest all files in input/
    python -m ip_sla_monitor charts            # Launch chart GUI
    python -m ip_sla_monitor status            # Show data status
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

from .config import BASE_DIR, INPUT_DIR, OUTPUT_FILE, LOG_FILE, LOG_FORMAT
from .parser import IPSLAParser
from .excel_handler import ExcelHandler
from .chart_manager import ChartManager

# GUI import is optional (requires tkinter)
try:
    from .gui import show_chart_gui
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    show_chart_gui = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def ingest_file(filepath: Path) -> tuple[int, int]:
    """
    Ingest a single data file into the Excel workbook.
    
    Args:
        filepath: Path to the raw data file
        
    Returns:
        Tuple of (records_added, records_skipped)
    """
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        return 0, 0
    
    logger.info(f"Ingesting file: {filepath}")
    
    # Parse the file
    parser = IPSLAParser()
    records = parser.parse_file(filepath)
    
    if not records:
        logger.warning("No records parsed from file")
        return 0, 0
    
    # Open Excel and append
    handler = ExcelHandler()
    handler.open_or_create()
    
    added, skipped = handler.append_records(records)
    
    # Sort by timestamp
    handler.sort_by_timestamp()
    
    handler.save()
    handler.close()
    
    return added, skipped


def ingest_all_files() -> tuple[int, int]:
    """
    Ingest all .txt files from the input directory.
    
    Returns:
        Tuple of (total_added, total_skipped)
    """
    # Create input directory if needed
    INPUT_DIR.mkdir(exist_ok=True)
    
    # Find all text files
    files = list(INPUT_DIR.glob("*.txt"))
    
    if not files:
        logger.info(f"No .txt files found in {INPUT_DIR}")
        return 0, 0
    
    logger.info(f"Found {len(files)} file(s) to process")
    
    total_added = 0
    total_skipped = 0
    
    for filepath in sorted(files):
        added, skipped = ingest_file(filepath)
        total_added += added
        total_skipped += skipped
    
    return total_added, total_skipped


def show_status() -> None:
    """Display current data status."""
    print(f"\n{'='*50}")
    print("IP SLA Monitor Status")
    print(f"{'='*50}")
    
    print(f"\nPaths:")
    print(f"  Base directory:  {BASE_DIR}")
    print(f"  Input directory: {INPUT_DIR}")
    print(f"  Output file:     {OUTPUT_FILE}")
    
    # Check input directory
    INPUT_DIR.mkdir(exist_ok=True)
    input_files = list(INPUT_DIR.glob("*.txt"))
    print(f"\nInput files pending: {len(input_files)}")
    for f in input_files[:5]:
        print(f"  - {f.name}")
    if len(input_files) > 5:
        print(f"  ... and {len(input_files) - 5} more")
    
    # Check Excel file
    if OUTPUT_FILE.exists():
        handler = ExcelHandler()
        handler.open_or_create()
        
        timestamps = handler.get_existing_timestamps()
        start, end = handler.get_data_range()
        
        handler.close()
        
        print(f"\nExcel Data:")
        print(f"  Total records: {len(timestamps)}")
        if start and end:
            print(f"  Date range:    {start.strftime('%Y-%m-%d %H:%M')} to {end.strftime('%Y-%m-%d %H:%M')}")
            span = end - start
            print(f"  Time span:     {span.days} days, {span.seconds // 3600} hours")
    else:
        print(f"\nExcel file not yet created")
    
    print(f"\n{'='*50}\n")


def generate_all_charts(start_str: str = None, end_str: str = None) -> None:
    """
    Generate all favorite charts from command line.
    
    Args:
        start_str: Optional start date string (YYYY-MM-DD)
        end_str: Optional end date string (YYYY-MM-DD)
    """
    start_date = None
    end_date = None
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid start date format: {start_str}")
            return
    
    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
        except ValueError:
            logger.error(f"Invalid end date format: {end_str}")
            return
    
    handler = ExcelHandler()
    handler.open_or_create()
    
    chart_mgr = ChartManager(handler.workbook)
    created = chart_mgr.create_all_favorite_charts(start_date, end_date)
    
    handler.save()
    handler.close()
    
    print(f"Created {len(created)} charts:")
    for name in created:
        print(f"  - {name}")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="IP SLA Monitor - Cisco IP SLA measurement tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m ip_sla_monitor ingest dataset.txt    Ingest a specific file
  python -m ip_sla_monitor ingest-all            Ingest all files in input/
  python -m ip_sla_monitor charts                Launch chart GUI
  python -m ip_sla_monitor charts-cli            Generate all charts (CLI)
  python -m ip_sla_monitor status                Show current status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest single file
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a single data file')
    ingest_parser.add_argument('file', type=Path, help='Path to the data file')
    
    # Ingest all files
    subparsers.add_parser('ingest-all', help='Ingest all .txt files from input directory')
    
    # Chart GUI
    subparsers.add_parser('charts', help='Launch chart generation GUI')
    
    # Chart CLI
    charts_cli = subparsers.add_parser('charts-cli', help='Generate all charts from command line')
    charts_cli.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    charts_cli.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    
    # Status
    subparsers.add_parser('status', help='Show data status')
    
    args = parser.parse_args()
    
    if args.command == 'ingest':
        added, skipped = ingest_file(args.file)
        print(f"Ingested: {added} added, {skipped} skipped (duplicates)")
        
    elif args.command == 'ingest-all':
        added, skipped = ingest_all_files()
        print(f"Total: {added} added, {skipped} skipped (duplicates)")
        
    elif args.command == 'charts':
        if GUI_AVAILABLE:
            show_chart_gui()
        else:
            print("GUI not available (tkinter not installed).")
            print("Use 'charts-cli' for command-line chart generation.")
        
    elif args.command == 'charts-cli':
        generate_all_charts(args.start, args.end)
        
    elif args.command == 'status':
        show_status()
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
