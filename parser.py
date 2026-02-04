"""
Parser for Cisco IP SLA aggregated statistics output.

Extracts structured data from raw router output text.
"""

import re
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IPSLARecord:
    """Single IP SLA measurement interval record."""
    start_time: datetime
    min_mos: float
    max_mos: float
    min_icpif: float
    max_icpif: float
    num_rtt: int
    rtt_min_ms: int
    rtt_avg_ms: int
    rtt_max_ms: int
    rtt_over_threshold_count: int
    rtt_over_threshold_pct: int
    num_oneway_samples: int
    jitter_sd_avg_ms: int
    jitter_sd_max_ms: int
    jitter_ds_avg_ms: int
    jitter_ds_max_ms: int
    loss_sd: int
    loss_ds: int
    packet_late_arrival: int
    out_of_seq: int
    tail_drop: int
    successes: int
    failures: int

    def to_row(self) -> list:
        """Convert record to Excel row format."""
        return [
            self.start_time,
            self.min_mos,
            self.max_mos,
            self.min_icpif,
            self.max_icpif,
            self.num_rtt,
            self.rtt_min_ms,
            self.rtt_avg_ms,
            self.rtt_max_ms,
            self.rtt_over_threshold_count,
            self.rtt_over_threshold_pct,
            self.num_oneway_samples,
            self.jitter_sd_avg_ms,
            self.jitter_sd_max_ms,
            self.jitter_ds_avg_ms,
            self.jitter_ds_max_ms,
            self.loss_sd,
            self.loss_ds,
            self.packet_late_arrival,
            self.out_of_seq,
            self.tail_drop,
            self.successes,
            self.failures
        ]


class IPSLAParser:
    """
    Parser for Cisco IP SLA 'show ip sla statistics aggregated' output.
    
    Handles the text output format from Cisco routers and extracts
    all measurement intervals into structured records.
    """

    # Regex patterns for parsing
    PATTERNS = {
        # Start Time Index: 09:28:16 EST Wed Jan 28 2026
        'start_time': re.compile(
            r'Start Time Index:\s+(\d{2}:\d{2}:\d{2})\s+\w+\s+(\w+)\s+(\w+)\s+(\d+)\s+(\d{4})'
        ),
        # MinOfICPIF: 1   MaxOfICPIF: 77  MinOfMOS: 1.51  MaxOfMOS: 4.34
        'voice_scores': re.compile(
            r'MinOfICPIF:\s*([\d.]+)\s+MaxOfICPIF:\s*([\d.]+)\s+MinOfMOS:\s*([\d.]+)\s+MaxOfMOS:\s*([\d.]+)'
        ),
        # Number Of RTT: 59109            RTT Min/Avg/Max: 8/120/2332 milliseconds
        'rtt_values': re.compile(
            r'Number Of RTT:\s*(\d+)\s+RTT Min/Avg/Max:\s*(\d+)/(\d+)/(\d+)'
        ),
        # Number of Latency one-way Samples: 0
        'oneway_samples': re.compile(
            r'Number of Latency one-way Samples:\s*(\d+)'
        ),
        # Number Of RTT Over Threshold: 9528 (16%)
        'rtt_threshold': re.compile(
            r'Number Of RTT Over Threshold:\s*(\d+)\s*\((\d+)%\)'
        ),
        # Source to Destination Jitter Min/Avg/Max: 0/5/468 milliseconds
        'jitter_sd': re.compile(
            r'Source to Destination Jitter Min/Avg/Max:\s*(\d+)/(\d+)/(\d+)'
        ),
        # Destination to Source Jitter Min/Avg/Max: 0/4/64 milliseconds
        'jitter_ds': re.compile(
            r'Destination to Source Jitter Min/Avg/Max:\s*(\d+)/(\d+)/(\d+)'
        ),
        # Loss Source to Destination: 0
        'loss_sd': re.compile(
            r'Loss Source to Destination:\s*(\d+)'
        ),
        # Loss Destination to Source: 122
        'loss_ds': re.compile(
            r'Loss Destination to Source:\s*(\d+)'
        ),
        # Out Of Sequence: 0      Tail Drop: 39
        'out_of_seq_tail': re.compile(
            r'Out Of Sequence:\s*(\d+)\s+Tail Drop:\s*(\d+)'
        ),
        # Packet Late Arrival: 730        Packet Skipped: 0
        'late_arrival': re.compile(
            r'Packet Late Arrival:\s*(\d+)'
        ),
        # Number of successes: 60
        'successes': re.compile(
            r'Number of successes:\s*(\d+)'
        ),
        # Number of failures: 1
        'failures': re.compile(
            r'Number of failures:\s*(\d+)'
        ),
    }

    # Month name to number mapping
    MONTHS = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    def __init__(self):
        self.records: List[IPSLARecord] = []

    def parse_file(self, filepath: Path) -> List[IPSLARecord]:
        """
        Parse an IP SLA output file and return list of records.
        
        Args:
            filepath: Path to the input file
            
        Returns:
            List of IPSLARecord objects
        """
        logger.info(f"Parsing file: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        return self.parse_content(content)

    def parse_content(self, content: str) -> List[IPSLARecord]:
        """
        Parse IP SLA output content string.
        
        Args:
            content: Raw text content from router output
            
        Returns:
            List of IPSLARecord objects
        """
        records = []
        
        # Split content into blocks by "Start Time Index"
        blocks = re.split(r'(?=Start Time Index:)', content)
        
        for block in blocks:
            if not block.strip() or 'Start Time Index:' not in block:
                continue
            
            record = self._parse_block(block)
            if record:
                records.append(record)
                logger.debug(f"Parsed record: {record.start_time}")
        
        logger.info(f"Parsed {len(records)} records")
        return records

    def _parse_block(self, block: str) -> Optional[IPSLARecord]:
        """
        Parse a single measurement block.
        
        Args:
            block: Text block for one measurement interval
            
        Returns:
            IPSLARecord or None if parsing fails
        """
        try:
            # Extract start time
            match = self.PATTERNS['start_time'].search(block)
            if not match:
                logger.warning("Could not parse start time from block")
                return None
            
            time_str, day_name, month_str, day, year = match.groups()
            hour, minute, second = map(int, time_str.split(':'))
            month = self.MONTHS.get(month_str, 1)
            start_time = datetime(int(year), month, int(day), hour, minute, second)

            # Extract voice scores
            match = self.PATTERNS['voice_scores'].search(block)
            if match:
                min_icpif, max_icpif, min_mos, max_mos = map(float, match.groups())
            else:
                min_icpif = max_icpif = min_mos = max_mos = 0.0

            # Extract RTT values
            match = self.PATTERNS['rtt_values'].search(block)
            if match:
                num_rtt, rtt_min, rtt_avg, rtt_max = map(int, match.groups())
            else:
                num_rtt = rtt_min = rtt_avg = rtt_max = 0

            # Extract one-way samples
            match = self.PATTERNS['oneway_samples'].search(block)
            num_oneway = int(match.group(1)) if match else 0

            # Extract RTT threshold
            match = self.PATTERNS['rtt_threshold'].search(block)
            if match:
                rtt_threshold_count, rtt_threshold_pct = map(int, match.groups())
            else:
                rtt_threshold_count = rtt_threshold_pct = 0

            # Extract SD jitter
            match = self.PATTERNS['jitter_sd'].search(block)
            if match:
                _, jitter_sd_avg, jitter_sd_max = map(int, match.groups())
            else:
                jitter_sd_avg = jitter_sd_max = 0

            # Extract DS jitter
            match = self.PATTERNS['jitter_ds'].search(block)
            if match:
                _, jitter_ds_avg, jitter_ds_max = map(int, match.groups())
            else:
                jitter_ds_avg = jitter_ds_max = 0

            # Extract loss SD
            match = self.PATTERNS['loss_sd'].search(block)
            loss_sd = int(match.group(1)) if match else 0

            # Extract loss DS
            match = self.PATTERNS['loss_ds'].search(block)
            loss_ds = int(match.group(1)) if match else 0

            # Extract out of sequence and tail drop
            match = self.PATTERNS['out_of_seq_tail'].search(block)
            if match:
                out_of_seq, tail_drop = map(int, match.groups())
            else:
                out_of_seq = tail_drop = 0

            # Extract late arrival
            match = self.PATTERNS['late_arrival'].search(block)
            late_arrival = int(match.group(1)) if match else 0

            # Extract successes
            match = self.PATTERNS['successes'].search(block)
            successes = int(match.group(1)) if match else 0

            # Extract failures
            match = self.PATTERNS['failures'].search(block)
            failures = int(match.group(1)) if match else 0

            return IPSLARecord(
                start_time=start_time,
                min_mos=min_mos,
                max_mos=max_mos,
                min_icpif=min_icpif,
                max_icpif=max_icpif,
                num_rtt=num_rtt,
                rtt_min_ms=rtt_min,
                rtt_avg_ms=rtt_avg,
                rtt_max_ms=rtt_max,
                rtt_over_threshold_count=rtt_threshold_count,
                rtt_over_threshold_pct=rtt_threshold_pct,
                num_oneway_samples=num_oneway,
                jitter_sd_avg_ms=jitter_sd_avg,
                jitter_sd_max_ms=jitter_sd_max,
                jitter_ds_avg_ms=jitter_ds_avg,
                jitter_ds_max_ms=jitter_ds_max,
                loss_sd=loss_sd,
                loss_ds=loss_ds,
                packet_late_arrival=late_arrival,
                out_of_seq=out_of_seq,
                tail_drop=tail_drop,
                successes=successes,
                failures=failures
            )

        except Exception as e:
            logger.error(f"Error parsing block: {e}")
            return None
