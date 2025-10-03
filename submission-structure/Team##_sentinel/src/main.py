#!/usr/bin/env python3
"""Main processing pipeline for Project Sentinel event detection."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from data_loader import load_all_data
from event_detector import (
    detect_scanner_avoidance,
    detect_barcode_switching,
    detect_weight_discrepancies,
    detect_long_queues,
    detect_long_wait_times,
    detect_system_crashes,
    detect_inventory_discrepancies,
    detect_success_operations
)


def process_events(data_dir: Path, output_file: Path) -> None:
    """Process all events and generate output file.
    
    Args:
        data_dir: Path to input data directory
        output_file: Path to output events.jsonl file
    """
    print(f"Loading data from {data_dir}...")
    data = load_all_data(data_dir)
    
    print("Detecting events...")
    all_detected_events = []
    
    # Detect various event types
    print("  - Detecting scanner avoidance...")
    all_detected_events.extend(
        detect_scanner_avoidance(data['pos_transactions'], data['rfid_readings'])
    )
    
    print("  - Detecting barcode switching...")
    all_detected_events.extend(
        detect_barcode_switching(data['pos_transactions'], data['product_recognition'])
    )
    
    print("  - Detecting weight discrepancies...")
    all_detected_events.extend(
        detect_weight_discrepancies(data['pos_transactions'], data['products_list'])
    )
    
    print("  - Detecting long queues...")
    all_detected_events.extend(
        detect_long_queues(data['queue_monitoring'])
    )
    
    print("  - Detecting long wait times...")
    all_detected_events.extend(
        detect_long_wait_times(data['queue_monitoring'])
    )
    
    # Combine all events for crash detection
    all_events = (
        data['pos_transactions'] + 
        data['rfid_readings'] + 
        data['queue_monitoring'] + 
        data['product_recognition']
    )
    
    print("  - Detecting system crashes...")
    all_detected_events.extend(
        detect_system_crashes(all_events)
    )
    
    print("  - Detecting inventory discrepancies...")
    all_detected_events.extend(
        detect_inventory_discrepancies(data['inventory_snapshots'], data['pos_transactions'])
    )
    
    print("  - Detecting success operations...")
    all_detected_events.extend(
        detect_success_operations(data['pos_transactions'], data['rfid_readings'])
    )
    
    # Sort events by timestamp
    all_detected_events.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))
    
    # Reassign event IDs in sequential order
    for idx, event in enumerate(all_detected_events):
        event['event_id'] = f'E{idx:03d}'
    
    # Write output
    print(f"Writing {len(all_detected_events)} events to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for event in all_detected_events:
            f.write(json.dumps(event) + '\n')
    
    print(f"Done! Generated {len(all_detected_events)} events.")


def main():
    """Main entry point for the processing pipeline."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python main.py <input_dir> <output_file>")
        print("Example: python main.py ../../../data/input output/events.jsonl")
        sys.exit(1)
    
    data_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    
    if not data_dir.exists():
        print(f"Error: Input directory not found: {data_dir}")
        sys.exit(1)
    
    process_events(data_dir, output_file)


if __name__ == '__main__':
    main()
