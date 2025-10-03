import socket
import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict

# --- Configuration ---
HOST = '127.0.0.1'
PORT = 8765
OUTPUT_FILE = 'events.jsonl'
ERROR_LOG_FILE = 'error.log'
PRODUCT_DATA_FILE = 'data/input/products_list.csv'
INVENTORY_SNAPSHOT_FILE = 'data/input/inventory_snapshots.jsonl'

# --- State Tracking ---
last_rfid_reads = defaultdict(lambda: {'datetime': None, 'sku': None})
last_product_recognition = defaultdict(lambda: {'datetime': None, 'sku': None})
inventory_levels = {}

# --- Utility Functions ---
def log_error(message):
    """Writes an error message to the error log file."""
    with open(ERROR_LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now()}] {message}\n")

# --- Data Loading ---
def load_csv_data(filepath):
    data = {}
    try:
        with open(filepath, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            if not reader.fieldnames: return None
            key_field = reader.fieldnames[0]
            for row in reader:
                if key := row.get(key_field): data[key] = row
    except FileNotFoundError:
        log_error(f"FATAL: Could not find {filepath}")
        return None
    return data

def load_initial_inventory():
    global inventory_levels
    try:
        with open(INVENTORY_SNAPSHOT_FILE, 'r') as f:
            snapshot = json.load(f)
            inventory_levels = snapshot.get('data', {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log_error(f"FATAL: Could not load initial inventory: {e}")

# --- Event Detection Algorithms ---

# @algorithm Scanner Avoidance | Detects when an item is read by RFID but not scanned at POS.
def detect_scanner_avoidance(stream_data):
    dataset = stream_data.get('dataset')
    event_payload = stream_data.get('event', {})
    station_id = event_payload.get('station_id')
    if not station_id: return None

    if dataset == 'RFID_data':
        if event_payload.get('data', {}).get('location') == 'IN_SCAN_AREA':
            last_rfid_reads[station_id] = {
                'datetime': stream_data.get('datetime'),
                'sku': event_payload.get('data', {}).get('sku')
            }
    elif dataset == 'POS_Transactions':
        pos_data = event_payload.get('data', {})
        last_read = last_rfid_reads[station_id]
        if last_read.get('sku') and last_read.get('sku') != pos_data.get('sku'):
            if stream_data.get('datetime') and last_read.get('datetime'):
                if stream_data['datetime'] - last_read['datetime'] < timedelta(seconds=5):
                    return {"timestamp": stream_data['timestamp'], "event_id": "E001", "event_data": {"event_name": "Scanner Avoidance", "station_id": station_id, "customer_id": pos_data.get('customer_id'), "product_sku": last_read['sku']}}
    return None

# @algorithm Inventory Discrepancy | Detects differences between tracked and actual inventory.
def detect_inventory_discrepancy(stream_data):
    global inventory_levels
    dataset = stream_data.get('dataset')
    event_payload = stream_data.get('event', {})

    if dataset == 'POS_Transactions':
        if sku := event_payload.get('data', {}).get('sku'):
            if sku in inventory_levels: inventory_levels[sku] -= 1
    elif dataset == 'Current_inventory_data':
        snapshot_data = event_payload.get('data', {})
        for sku, actual_count in snapshot_data.items():
            if (expected := inventory_levels.get(sku)) is not None and abs(expected - actual_count) > 5:
                inventory_levels[sku] = actual_count # Resync
                return {"timestamp": stream_data['timestamp'], "event_id": "E007", "event_data": {"event_name": "Inventory Discrepancy", "SKU": sku, "Expected_Inventory": expected, "Actual_Inventory": actual_count}}
    return None

# @algorithm Long Queue Length | Detects when the number of customers in a queue exceeds a threshold.
def detect_long_queue(stream_data):
    if stream_data.get('dataset') == 'Queue_monitor':
        event_payload = stream_data.get('event', {})
        if (count := event_payload.get('data', {}).get('customer_count', 0)) > 5:
            return {"timestamp": stream_data['timestamp'], "event_id": "E005", "event_data": {"event_name": "Long Queue Length", "station_id": event_payload['station_id'], "num_of_customers": count}}
    return None

# @algorithm Long Wait Time | Detects when the average customer wait time exceeds a threshold.
def detect_long_wait_time(stream_data):
    if stream_data.get('dataset') == 'Queue_monitor':
        event_payload = stream_data.get('event', {})
        if (dwell := event_payload.get('data', {}).get('average_dwell_time', 0)) > 300:
            return {"timestamp": stream_data['timestamp'], "event_id": "E006", "event_data": {"event_name": "Long Wait Time", "station_id": event_payload['station_id'], "wait_time_seconds": dwell}}
    return None

# @algorithm Weight Discrepancies | Detects when the weight of a scanned item differs from its expected weight.
def detect_weight_discrepancy(stream_data, products):
    """Compares transaction weight with product catalog weight."""
    if stream_data.get('dataset') == 'POS_Transactions':
        event_payload = stream_data.get('event', {})
        pos_data = event_payload.get('data', {})
        sku = pos_data.get('sku')
        actual_weight = pos_data.get('weight_g')

        if sku and actual_weight is not None and sku in products:
            try:
                expected_weight = float(products[sku]['weight'])
                if not (expected_weight * 0.95 <= actual_weight <= expected_weight * 1.05):
                    return {
                        "timestamp": stream_data['timestamp'],
                        "event_id": "E003",
                        "event_data": {
                            "event_name": "Weight Discrepancies",
                            "station_id": event_payload.get('station_id'),
                            "customer_id": pos_data.get('customer_id'),
                            "product_sku": sku,
                            "expected_weight": expected_weight,
                            "actual_weight": actual_weight
                        }
                    }
            except (ValueError, KeyError) as e:
                log_error(f"Could not process weight for SKU {sku}: {e}")
    return None

# @algorithm Barcode Switching | Detects when a vision system prediction is followed by a different item scan.
def detect_barcode_switching(stream_data):
    """Detects potential barcode switching using vision and POS data."""
    dataset = stream_data.get('dataset')
    event_payload = stream_data.get('event', {})
    station_id = event_payload.get('station_id')
    if not station_id: return None

    if dataset == 'Product_recognism':
        last_product_recognition[station_id] = {
            'datetime': stream_data.get('datetime'),
            'sku': event_payload.get('data', {}).get('predicted_product')
        }
    elif dataset == 'POS_Transactions':
        pos_data = event_payload.get('data', {})
        last_rec = last_product_recognition[station_id]
        if last_rec.get('sku') and last_rec.get('sku') != pos_data.get('sku'):
            if stream_data.get('datetime') and last_rec.get('datetime'):
                if stream_data['datetime'] - last_rec['datetime'] < timedelta(seconds=5):
                    return {
                        "timestamp": stream_data['timestamp'],
                        "event_id": "E002",
                        "event_data": {
                            "event_name": "Barcode Switching",
                            "station_id": station_id,
                            "customer_id": pos_data.get('customer_id'),
                            "actual_sku": last_rec['sku'],
                            "scanned_sku": pos_data.get('sku')
                        }
                    }
    return None

# --- Main Application Logic ---
def main():
    print("Initializing...")
    load_initial_inventory()
    products = load_csv_data(PRODUCT_DATA_FILE)
    if not products or not inventory_levels:
        print("FATAL: Failed to load critical data. Exiting.")
        return

    # Clear previous log files
    open(OUTPUT_FILE, 'w').close()
    open(ERROR_LOG_FILE, 'w').close()

    detectors = [
        detect_scanner_avoidance,
        detect_inventory_discrepancy,
        detect_long_queue,
        detect_long_wait_time,
        lambda stream_data: detect_weight_discrepancy(stream_data, products),
        detect_barcode_switching
    ]

    print(f"Connecting to stream at {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s, open(OUTPUT_FILE, 'a') as outfile:
            s.connect((HOST, PORT))
            sock_file = s.makefile('r', encoding='utf-8')
            print("Connection successful.")

            # The first line is a banner, read and discard it.
            banner = sock_file.readline()
            print(f"Skipped banner: {banner.strip()}")

            # Process the stream line by line
            for line in sock_file:
                try:
                    stream_data = json.loads(line)

                    if 'timestamp' in stream_data:
                        stream_data['datetime'] = datetime.strptime(stream_data['timestamp'], "%Y-%m-%dT%H:%M:%S")

                    for detector in detectors:
                        event = detector(stream_data)
                        if event:
                            print(f"EVENT DETECTED: {event['event_data']['event_name']}")
                            outfile.write(json.dumps(event) + '\n')
                            outfile.flush()

                except json.JSONDecodeError as e:
                    log_error(f"JSON decode error on line: '{line.strip()}'. Error: {e}")
                except Exception as e:
                    log_error(f"An unexpected error occurred: {e}")

    except ConnectionRefusedError:
        log_error(f"Connection refused. Is the server running at {HOST}:{PORT}?")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("Processing complete.")

if __name__ == "__main__":
    main()