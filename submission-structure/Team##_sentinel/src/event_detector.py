#!/usr/bin/env python3
"""Event detection algorithms for Project Sentinel."""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict


# @algorithm Scanner Avoidance Detection | Detects when customers avoid scanning products by comparing RFID and POS data
def detect_scanner_avoidance(
    pos_transactions: List[Dict[str, Any]],
    rfid_readings: List[Dict[str, Any]],
    time_window_seconds: int = 10
) -> List[Dict[str, Any]]:
    """Detect scanner avoidance by comparing RFID readings with POS transactions.
    
    Args:
        pos_transactions: List of POS transaction events
        rfid_readings: List of RFID reading events
        time_window_seconds: Time window to correlate events
        
    Returns:
        List of scanner avoidance events
    """
    events = []
    event_counter = 0
    
    # Group RFID readings by customer/station/time
    rfid_by_station = defaultdict(list)
    for rfid in rfid_readings:
        if rfid.get('data', {}).get('location') == 'IN_SCAN_AREA':
            rfid_by_station[rfid['station_id']].append(rfid)
    
    # Check each POS transaction
    for pos in pos_transactions:
        station_id = pos['station_id']
        customer_id = pos.get('data', {}).get('customer_id')
        pos_sku = pos.get('data', {}).get('sku')
        pos_time = datetime.fromisoformat(pos['timestamp'])
        
        # Find RFID readings in the same time window
        rfid_skus = set()
        for rfid in rfid_by_station.get(station_id, []):
            rfid_time = datetime.fromisoformat(rfid['timestamp'])
            time_diff = abs((rfid_time - pos_time).total_seconds())
            if time_diff <= time_window_seconds:
                rfid_skus.add(rfid.get('data', {}).get('sku'))
        
        # Check for SKUs detected by RFID but not scanned
        unscanned_skus = rfid_skus - {pos_sku}
        for unscanned_sku in unscanned_skus:
            events.append({
                'timestamp': pos['timestamp'],
                'event_id': f'E{event_counter:03d}',
                'event_data': {
                    'event_name': 'Scanner Avoidance',
                    'station_id': station_id,
                    'customer_id': customer_id,
                    'product_sku': unscanned_sku
                }
            })
            event_counter += 1
    
    return events


# @algorithm Barcode Switching Detection | Detects when a different barcode is scanned than the product present
def detect_barcode_switching(
    pos_transactions: List[Dict[str, Any]],
    product_recognition: List[Dict[str, Any]],
    time_window_seconds: int = 5
) -> List[Dict[str, Any]]:
    """Detect barcode switching by comparing visual recognition with scanned barcodes.
    
    Args:
        pos_transactions: List of POS transaction events
        product_recognition: List of product recognition events
        time_window_seconds: Time window to correlate events
        
    Returns:
        List of barcode switching events
    """
    events = []
    event_counter = 0
    
    # Group product recognition by station
    recognition_by_station = defaultdict(list)
    for recog in product_recognition:
        if recog.get('data', {}).get('accuracy', 0) > 0.5:  # Only use confident predictions
            recognition_by_station[recog['station_id']].append(recog)
    
    # Check each POS transaction
    for pos in pos_transactions:
        station_id = pos['station_id']
        customer_id = pos.get('data', {}).get('customer_id')
        scanned_sku = pos.get('data', {}).get('sku')
        pos_time = datetime.fromisoformat(pos['timestamp'])
        
        # Find product recognition in the same time window
        for recog in recognition_by_station.get(station_id, []):
            recog_time = datetime.fromisoformat(recog['timestamp'])
            time_diff = abs((recog_time - pos_time).total_seconds())
            
            if time_diff <= time_window_seconds:
                predicted_sku = recog.get('data', {}).get('predicted_product')
                
                # If predicted SKU differs from scanned SKU, it's potential barcode switching
                if predicted_sku and predicted_sku != scanned_sku:
                    events.append({
                        'timestamp': pos['timestamp'],
                        'event_id': f'E{event_counter:03d}',
                        'event_data': {
                            'event_name': 'Barcode Switching',
                            'station_id': station_id,
                            'customer_id': customer_id,
                            'actual_sku': predicted_sku,
                            'scanned_sku': scanned_sku
                        }
                    })
                    event_counter += 1
                    break
    
    return events


# @algorithm Weight Discrepancy Detection | Detects when scanned product weight differs from expected weight
def detect_weight_discrepancies(
    pos_transactions: List[Dict[str, Any]],
    products_list: List[Dict[str, Any]],
    tolerance_percent: float = 20.0
) -> List[Dict[str, Any]]:
    """Detect weight discrepancies by comparing actual weights with expected weights.
    
    Args:
        pos_transactions: List of POS transaction events
        products_list: Product catalog with expected weights
        tolerance_percent: Acceptable weight variance percentage
        
    Returns:
        List of weight discrepancy events
    """
    events = []
    event_counter = 0
    
    # Create product weight lookup
    product_weights = {}
    for product in products_list:
        sku = product.get('SKU')
        weight = product.get('Weight (g)')
        if sku and weight:
            try:
                product_weights[sku] = float(weight)
            except (ValueError, TypeError):
                pass
    
    # Check each POS transaction
    for pos in pos_transactions:
        sku = pos.get('data', {}).get('sku')
        actual_weight = pos.get('data', {}).get('weight_g')
        customer_id = pos.get('data', {}).get('customer_id')
        station_id = pos['station_id']
        
        if sku in product_weights and actual_weight:
            expected_weight = product_weights[sku]
            weight_diff = abs(actual_weight - expected_weight)
            tolerance = expected_weight * (tolerance_percent / 100.0)
            
            if weight_diff > tolerance:
                events.append({
                    'timestamp': pos['timestamp'],
                    'event_id': f'E{event_counter:03d}',
                    'event_data': {
                        'event_name': 'Weight Discrepancies',
                        'station_id': station_id,
                        'customer_id': customer_id,
                        'product_sku': sku,
                        'expected_weight': int(expected_weight),
                        'actual_weight': int(actual_weight)
                    }
                })
                event_counter += 1
    
    return events


# @algorithm Long Queue Detection | Detects when queue length exceeds threshold
def detect_long_queues(
    queue_monitoring: List[Dict[str, Any]],
    threshold: int = 5
) -> List[Dict[str, Any]]:
    """Detect long queues when customer count exceeds threshold.
    
    Args:
        queue_monitoring: List of queue monitoring events
        threshold: Maximum acceptable queue length
        
    Returns:
        List of long queue events
    """
    events = []
    event_counter = 0
    
    for queue in queue_monitoring:
        customer_count = queue.get('data', {}).get('customer_count', 0)
        station_id = queue['station_id']
        
        if customer_count > threshold:
            events.append({
                'timestamp': queue['timestamp'],
                'event_id': f'E{event_counter:03d}',
                'event_data': {
                    'event_name': 'Long Queue Length',
                    'station_id': station_id,
                    'num_of_customers': customer_count
                }
            })
            event_counter += 1
    
    return events


# @algorithm Long Wait Time Detection | Detects when average wait time exceeds threshold
def detect_long_wait_times(
    queue_monitoring: List[Dict[str, Any]],
    threshold_seconds: float = 300.0
) -> List[Dict[str, Any]]:
    """Detect long wait times when dwell time exceeds threshold.
    
    Args:
        queue_monitoring: List of queue monitoring events
        threshold_seconds: Maximum acceptable wait time in seconds
        
    Returns:
        List of long wait time events
    """
    events = []
    event_counter = 0
    
    for queue in queue_monitoring:
        avg_dwell_time = queue.get('data', {}).get('average_dwell_time', 0)
        station_id = queue['station_id']
        
        if avg_dwell_time > threshold_seconds:
            events.append({
                'timestamp': queue['timestamp'],
                'event_id': f'E{event_counter:03d}',
                'event_data': {
                    'event_name': 'Long Wait Time',
                    'station_id': station_id,
                    'wait_time_seconds': int(avg_dwell_time)
                }
            })
            event_counter += 1
    
    return events


# @algorithm System Crash Detection | Detects system crashes based on status changes
def detect_system_crashes(
    all_events: List[Dict[str, Any]],
    gap_threshold_seconds: int = 120
) -> List[Dict[str, Any]]:
    """Detect system crashes by identifying large gaps in event streams.
    
    Args:
        all_events: All events sorted by timestamp
        gap_threshold_seconds: Minimum gap to consider as a crash
        
    Returns:
        List of system crash events
    """
    events = []
    event_counter = 0
    
    # Group events by station
    station_events = defaultdict(list)
    for event in all_events:
        station_id = event.get('station_id')
        if station_id:
            station_events[station_id].append(event)
    
    # Check for large gaps in each station
    for station_id, station_event_list in station_events.items():
        station_event_list.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))
        
        for i in range(len(station_event_list) - 1):
            current_time = datetime.fromisoformat(station_event_list[i]['timestamp'])
            next_time = datetime.fromisoformat(station_event_list[i + 1]['timestamp'])
            gap = (next_time - current_time).total_seconds()
            
            if gap >= gap_threshold_seconds:
                events.append({
                    'timestamp': station_event_list[i + 1]['timestamp'],
                    'event_id': f'E{event_counter:03d}',
                    'event_data': {
                        'event_name': 'Unexpected Systems Crash',
                        'station_id': station_id,
                        'duration_seconds': int(gap)
                    }
                })
                event_counter += 1
    
    return events


# @algorithm Inventory Discrepancy Detection | Detects differences between expected and actual inventory
def detect_inventory_discrepancies(
    inventory_snapshots: List[Dict[str, Any]],
    pos_transactions: List[Dict[str, Any]],
    threshold_percent: float = 10.0
) -> List[Dict[str, Any]]:
    """Detect inventory discrepancies by comparing snapshots with transaction history.
    
    Args:
        inventory_snapshots: Inventory snapshot events
        pos_transactions: POS transaction events
        threshold_percent: Acceptable variance percentage
        
    Returns:
        List of inventory discrepancy events
    """
    events = []
    event_counter = 0
    
    if not inventory_snapshots:
        return events
    
    # Get initial inventory snapshot
    initial_snapshot = inventory_snapshots[0]
    inventory_data = initial_snapshot.get('data', {})
    snapshot_time = datetime.fromisoformat(initial_snapshot['timestamp'])
    
    # Calculate expected inventory based on transactions
    expected_inventory = dict(inventory_data)
    
    for pos in pos_transactions:
        pos_time = datetime.fromisoformat(pos['timestamp'])
        if pos_time > snapshot_time:
            sku = pos.get('data', {}).get('sku')
            if sku in expected_inventory:
                expected_inventory[sku] -= 1
    
    # Compare with later snapshots or final expected inventory
    for sku, expected_qty in expected_inventory.items():
        actual_qty = inventory_data.get(sku, 0)
        if actual_qty > 0:
            variance_percent = abs(expected_qty - actual_qty) / actual_qty * 100
            
            if variance_percent > threshold_percent and abs(expected_qty - actual_qty) > 5:
                events.append({
                    'timestamp': initial_snapshot['timestamp'],
                    'event_id': f'E{event_counter:03d}',
                    'event_data': {
                        'event_name': 'Inventory Discrepancy',
                        'SKU': sku,
                        'Expected_Inventory': int(inventory_data[sku]),
                        'Actual_Inventory': int(expected_qty)
                    }
                })
                event_counter += 1
    
    return events


# @algorithm Success Operation Detection | Detects successful checkout operations
def detect_success_operations(
    pos_transactions: List[Dict[str, Any]],
    rfid_readings: List[Dict[str, Any]],
    time_window_seconds: int = 10
) -> List[Dict[str, Any]]:
    """Detect successful operations where POS and RFID data match.
    
    Args:
        pos_transactions: List of POS transaction events
        rfid_readings: List of RFID reading events
        time_window_seconds: Time window to correlate events
        
    Returns:
        List of success operation events
    """
    events = []
    event_counter = 0
    
    # Group RFID readings by station
    rfid_by_station = defaultdict(list)
    for rfid in rfid_readings:
        rfid_by_station[rfid['station_id']].append(rfid)
    
    # Check each POS transaction
    for pos in pos_transactions:
        station_id = pos['station_id']
        customer_id = pos.get('data', {}).get('customer_id')
        pos_sku = pos.get('data', {}).get('sku')
        pos_time = datetime.fromisoformat(pos['timestamp'])
        
        # Find matching RFID reading
        rfid_match = False
        for rfid in rfid_by_station.get(station_id, []):
            rfid_time = datetime.fromisoformat(rfid['timestamp'])
            rfid_sku = rfid.get('data', {}).get('sku')
            time_diff = abs((rfid_time - pos_time).total_seconds())
            
            if time_diff <= time_window_seconds and rfid_sku == pos_sku:
                rfid_match = True
                break
        
        if rfid_match:
            events.append({
                'timestamp': pos['timestamp'],
                'event_id': f'E{event_counter:03d}',
                'event_data': {
                    'event_name': 'Succes Operation',
                    'station_id': station_id,
                    'customer_id': customer_id,
                    'product_sku': pos_sku
                }
            })
            event_counter += 1
    
    return events
