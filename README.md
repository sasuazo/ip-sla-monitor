# IP SLA Monitor

A Python tool for ingesting Cisco IP SLA UDP-Jitter measurements and visualizing them in Excel.

## Features

- **Parse** raw Cisco `show ip sla statistics aggregated` output
- **Store** measurements in Excel with automatic deduplication
- **Generate** charts with predefined favorites:
  - RTT Average/Max over time
  - Packet Loss per interval
  - Jitter over time
  - MOS Score over time
  - RTT Over Threshold
- **GUI** for easy time range selection and chart generation

## Installation

```bash
# Navigate to parent directory
cd /path/to/parent

# Install dependencies
pip install -r ip_sla_monitor/requirements.txt
```

## Directory Structure

```
ip_sla_monitor/
├── input/                  # Drop raw data files here
├── Ip_SLA_measurements.xlsx  # Output Excel file (auto-created)
├── ip_sla_monitor.log      # Log file
├── config.py               # Configuration settings
├── parser.py               # Cisco output parser
├── excel_handler.py        # Excel operations
├── chart_manager.py        # Chart generation
├── gui.py                  # Tkinter GUI
├── main.py                 # CLI entry point
└── requirements.txt
```

## Usage

### 1. Ingest Data Files

Place your Cisco IP SLA output files (`.txt`) in the `input/` directory, then run:

```bash
# Ingest all files in input/
python -m ip_sla_monitor ingest-all

# Or ingest a specific file
python -m ip_sla_monitor ingest /path/to/dataset.txt
```

### 2. Generate Charts

**Using GUI (recommended):**
```bash
python -m ip_sla_monitor charts
```

The GUI allows you to:
- See current data range and record count
- Set custom time ranges with quick presets (24h, 7d, 30d)
- Select which charts to generate
- Open the Excel file directly

**Using CLI:**
```bash
# Generate all charts for all data
python -m ip_sla_monitor charts-cli

# Generate charts for specific date range
python -m ip_sla_monitor charts-cli --start 2026-01-27 --end 2026-01-28
```

### 3. Check Status

```bash
python -m ip_sla_monitor status
```

## Input File Format

The tool parses standard Cisco IOS `show ip sla statistics aggregated <id>` output:

```
6000-2901#sh ip sla statistics aggregated 1
IPSLAs aggregated statistics

IPSLA operation id: 1
Start Time Index: 09:28:16 EST Wed Jan 28 2026
Type of operation: udp-jitter
Voice Scores:
        MinOfICPIF: 1   MaxOfICPIF: 77  MinOfMOS: 1.51  MaxOfMOS: 4.34
RTT Values:
        Number Of RTT: 59109            RTT Min/Avg/Max: 8/120/2332 milliseconds
...
```

## Output Format

Excel columns match the provided CSV format:
- StartTime, MinMOS, MaxMOS, MinICPIF, MaxICPIF
- NumRTT, RTT_Min_ms, RTT_Avg_ms, RTT_Max_ms
- RTT_Over_Threshold_Count, RTT_Over_Threshold_Pct
- Jitter metrics, Loss metrics, etc.

## Customization

Edit `config.py` to:
- Change file paths
- Add/modify chart favorites
- Adjust column definitions

## macOS Notes

- The GUI uses tkinter (included with Python on macOS)
- Excel files open with the default application (Excel or Numbers)
- All paths use forward slashes, compatible with macOS/Linux/Windows
