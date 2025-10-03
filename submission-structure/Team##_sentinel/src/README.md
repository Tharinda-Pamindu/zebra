# Project Sentinel Event Detection - Source Code

This directory contains the Python implementation for detecting various events in the Project Sentinel retail monitoring system.

## Module Structure

- **data_loader.py** - Data ingestion module for reading JSONL and CSV files
- **event_detector.py** - Event detection algorithms for fraud, operational issues, and system problems
- **main.py** - Main processing pipeline that coordinates all detection algorithms

## Event Detection Algorithms

The system implements the following detection algorithms:

1. **Scanner Avoidance Detection** - Detects products detected by RFID but not scanned at POS
2. **Barcode Switching Detection** - Identifies mismatches between visual recognition and scanned barcodes
3. **Weight Discrepancy Detection** - Flags products with significant weight differences from expected values
4. **Long Queue Detection** - Alerts when queue length exceeds threshold
5. **Long Wait Time Detection** - Identifies excessive customer wait times
6. **System Crash Detection** - Detects system outages based on event stream gaps
7. **Inventory Discrepancy Detection** - Finds differences between expected and actual inventory levels
8. **Success Operation Detection** - Records successful checkout operations with matching data

## Usage

### Direct Execution

```bash
cd src
python3 main.py <input_dir> <output_file>
```

Example:
```bash
python3 main.py ../../../data/input output/events.jsonl
```

### Via Automation Script

The recommended approach is to use the automation script:

```bash
cd evidence/executables
python3 run_demo.py [data_dir] [output_dir]
```

If no arguments are provided, it defaults to using the sample data in `data/input`.

## Dependencies

The implementation uses only Python standard library modules:
- json
- csv
- pathlib
- datetime
- collections
- subprocess

No external packages are required.

## Output Format

Events are written to a JSONL (JSON Lines) file where each line contains:

```json
{
  "timestamp": "2025-08-13T16:00:00",
  "event_id": "E000",
  "event_data": {
    "event_name": "Event Type",
    "station_id": "SCC1",
    ...additional fields...
  }
}
```

Events are sorted chronologically and assigned sequential IDs.
