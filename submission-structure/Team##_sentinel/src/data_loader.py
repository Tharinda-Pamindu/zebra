#!/usr/bin/env python3
"""Data loader module for reading streaming data sources."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load events from a JSONL file.
    
    Args:
        file_path: Path to the JSONL file
        
    Returns:
        List of event dictionaries
    """
    events = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def load_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of row dictionaries
    """
    import csv
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp string to datetime object.
    
    Args:
        ts_str: Timestamp string in ISO format
        
    Returns:
        datetime object
    """
    return datetime.fromisoformat(ts_str)


def load_all_data(data_dir: Path) -> Dict[str, Any]:
    """Load all data sources from the input directory.
    
    Args:
        data_dir: Path to the input data directory
        
    Returns:
        Dictionary containing all loaded data
    """
    data = {
        'pos_transactions': load_jsonl(data_dir / 'pos_transactions.jsonl'),
        'rfid_readings': load_jsonl(data_dir / 'rfid_readings.jsonl'),
        'queue_monitoring': load_jsonl(data_dir / 'queue_monitoring.jsonl'),
        'product_recognition': load_jsonl(data_dir / 'product_recognition.jsonl'),
        'inventory_snapshots': load_jsonl(data_dir / 'inventory_snapshots.jsonl'),
        'products_list': load_csv(data_dir / 'products_list.csv'),
        'customer_data': load_csv(data_dir / 'customer_data.csv'),
    }
    
    # Sort all event streams by timestamp
    for key in ['pos_transactions', 'rfid_readings', 'queue_monitoring', 'product_recognition']:
        data[key].sort(key=lambda x: parse_timestamp(x['timestamp']))
    
    return data
