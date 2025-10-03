# Evidence Directory

This directory contains evidence and outputs for Project Sentinel submission.

## Structure

- **executables/** - Automation scripts including `run_demo.py`
- **output/** - Generated event detection outputs
  - **test/** - Events detected from test dataset
  - **final/** - Events detected from final dataset
- **screenshots/** - Dashboard and system screenshots (PNG format)

## Running the Automation Script

To regenerate the output files:

```bash
cd executables
python3 run_demo.py [data_dir] [output_dir]
```

### Default Usage (using sample data)

```bash
python3 run_demo.py
```

This will process data from `data/input` and generate output in `evidence/output/test/`.

### Custom Data

```bash
python3 run_demo.py /path/to/test/data evidence/output/test
python3 run_demo.py /path/to/final/data evidence/output/final
```

## Requirements

- Python 3.9 or higher
- No external dependencies (uses only standard library)

## Output Format

The generated `events.jsonl` files contain one JSON object per line with the following structure:

```json
{
  "timestamp": "2025-08-13T16:00:00",
  "event_id": "E000",
  "event_data": {
    "event_name": "Event Type",
    ...additional fields...
  }
}
```

Events are sorted chronologically and assigned sequential IDs.
