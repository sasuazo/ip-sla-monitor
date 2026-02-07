# IP SLA Monitor

A Python tool for ingesting Cisco IP SLA UDP-Jitter measurements and generating publication-quality charts.

## Features

- **Parse** raw Cisco `show ip sla statistics aggregated` output
- **Store** measurements in Excel with automatic deduplication
- **Auto-cleanup** - input files deleted after successful ingestion
- **Generate** high-quality matplotlib charts:
  - RTT Average/Max over time
  - Jitter, One-Way Latency & Packet Loss (3-panel)
  - MOS Score over time
- **GUI** for easy time range selection and chart generation
- **CLI** for scripting and automation

## Installation

### macOS (with Homebrew Python)

```bash
# Clone or extract the project
cd ip-sla-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Other Systems

```bash
pip install -r requirements.txt
```

### As a Package (optional)

```bash
pip install -e .
```

## Directory Structure

```
ip_sla_monitor/
├── input/                      # Drop raw data files here (deleted after ingestion)
├── charts/                     # Generated PNG charts (auto-created)
├── Ip_SLA_measurements.xlsx    # Output Excel file (auto-created)
├── ip_sla_monitor.log          # Log file
├── config.py                   # Configuration settings
├── parser.py                   # Cisco output parser
├── excel_handler.py            # Excel operations
├── plotter.py                  # Matplotlib chart generation
├── chart_manager.py            # Excel chart generation (legacy)
├── gui.py                      # Tkinter GUI
├── main.py                     # CLI entry point
├── samples/                    # Example data files
├── pyproject.toml              # Package configuration
├── requirements.txt            # Dependencies
└── LICENSE                     # MIT License
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

> **Note:** Files are automatically deleted after successful ingestion.

### 2. Generate Charts

**Using CLI (recommended):**
```bash
# Generate all PNG charts
python -m ip_sla_monitor plot

# Generate and display interactively
python -m ip_sla_monitor plot --show

# Generate for specific date range
python -m ip_sla_monitor plot --start 2026-01-27 --end 2026-01-28
```

Charts are saved to the `charts/` folder as PNG files.

**Using GUI:**
```bash
python -m ip_sla_monitor charts
```

The GUI allows you to:
- See current data range and record count
- Set custom time ranges with quick presets (24h, 7d, 30d)
- Select which charts to generate
- Open the charts folder or Excel file directly

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

See `samples/example_dataset.txt` for a complete example.

## Output

### Excel Data

Excel columns include:
- StartTime, MinMOS, MaxMOS, MinICPIF, MaxICPIF
- NumRTT, RTT_Min_ms, RTT_Avg_ms, RTT_Max_ms
- RTT_Over_Threshold_Count, RTT_Over_Threshold_Pct
- Jitter metrics (SD/DS Avg/Max)
- Packet loss metrics (Loss_SD, Loss_DS, Late Arrival, TailDrop)
- Successes, Failures

### Charts

Generated PNG charts in `charts/` folder:
- `ip_sla_rtt.png` - RTT Average and Maximum over time
- `ip_sla_jitter_latency_loss.png` - 3-panel: Jitter, Latency, Packet Loss
- `ip_sla_mos.png` - MOS Score with quality threshold lines

## Customization

Edit `config.py` to:
- Change file paths (INPUT_DIR, OUTPUT_FILE)
- Adjust column definitions

Edit `plotter.py` to:
- Customize chart colors and styling
- Add new chart types

## macOS Notes

- Requires virtual environment (Homebrew Python restriction)
- Activate venv each session: `source venv/bin/activate`
- GUI uses tkinter (included with Python)
- Charts and Excel open with default applications

## License

MIT License - see LICENSE file
