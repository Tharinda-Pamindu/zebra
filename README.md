# Project Sentinel: Retail Intelligence System

## Overview

**Project Sentinel** is a comprehensive retail intelligence system designed to address critical challenges in the modern retail environment, including inventory shrinkage, operational inefficiencies, and poor customer experiences. By processing and analyzing real-time data streams from various in-store sensors, Project Sentinel provides actionable insights to optimize store performance, enhance security, and improve customer satisfaction.

This system is particularly focused on the challenges introduced by self-checkout systems, such as scan avoidance, barcode switching, and weight discrepancies.

-----

## Key Features

  * **Real-time Event Detection**: Identifies critical incidents as they happen, including potential theft, operational bottlenecks, and system failures.
  * **Multi-Source Data Integration**: Correlates data from RFID readers, POS systems, queue monitoring cameras, and product recognition systems to provide a holistic view of store operations.
  * **Actionable Insights**: Delivers insights for resource allocation, such as optimizing staff schedules and dynamically managing the number of open checkout stations.
  * **Live Dashboard**: A web-based interface that provides a real-time overview of store status, highlights anomalies, and visualizes key metrics.

-----

## System Architecture

The Project Sentinel system is composed of the following key components:

1.  **Data Ingestion (`data_loader.py`)**: This module is responsible for loading data from various sources, including JSONL files for event streams and CSV files for reference data like product and customer information.

2.  **Event Detection Engine (`event_detector.py`)**: The core of the system, this component houses the algorithms that analyze the incoming data to detect a range of predefined events.

3.  **Processing Pipeline (`main.py`)**: The main application orchestrates the data flow from ingestion to event detection and finally to output generation. It ensures that all data is processed and that the detected events are sorted and formatted correctly.

4.  **Data Streaming Simulator (`stream_server.py`)**: For development and testing, a simulator mimics the real-time data streams from in-store sensors. It can be configured for speed and can loop datasets for continuous testing.

5.  **Visualization Dashboard (`dashboard/app.py`)**: A Flask-based web application that provides a live feed of detected events, offering a user-friendly interface for monitoring store activity.

-----

## Event Detection Algorithms

Project Sentinel can detect a variety of events, which are categorized as follows:

### Fraud and Theft Detection

  * **Scanner Avoidance**: Detects when an item is read by the RFID system but is not scanned at the Point-of-Sale (POS) terminal.
  * **Barcode Switching**: Identifies instances where the product identified by the vision system does not match the product scanned at the POS.
  * **Weight Discrepancies**: Flags transactions where the measured weight of an item does not match its expected weight within a given tolerance.

### Operational and Customer Experience

  * **Long Queue Length**: Triggers an alert when the number of customers waiting in a queue exceeds a predefined threshold.
  * **Long Wait Time**: Detects when the average customer wait time surpasses a set limit.

### System and Inventory Management

  * **Unexpected System Crash**: Identifies when a system, such as a self-checkout station, stops sending data, indicating a potential crash or malfunction.
  * **Inventory Discrepancy**: Detects differences between the expected inventory levels (based on sales data) and the actual inventory levels from snapshots.

-----

## Getting Started

### Prerequisites

  * Python 3.9 or higher

### Installation & Running the Demo

1.  **Clone the repository (if applicable)**
2.  **Install Dependencies**: The core application has no external dependencies. The dashboard requires Flask, which can be installed via pip:
    ```bash
    pip install -r src/dashboard/requirements.txt
    ```
3.  **Run the demo**: The `run_demo.py` script automates the process of starting the data streamer, running the event detection, and generating the output.
    ```bash
    cd Team01_sentinel/evidence/executables/
    python run_demo.py
    ```

-----

## Usage

The system can be run in two modes:

1.  **Live Streaming Mode**: This mode uses the `stream_server.py` to simulate a real-time data feed. The `main.py` script connects to this stream and processes the data as it arrives.
2.  **Batch Processing Mode**: The `main.py` script can also process data from a directory of input files. This is useful for testing and validation.
    ```bash
    python src/main.py <input_directory> <output_file>
    ```

-----

## Data Sources

The system processes data from the following sources:

  * **POS Transactions** (`pos_transactions.jsonl`): Transactional data from the checkout counters.
  * **RFID Readings** (`rfid_readings.jsonl`): Data from RFID tags on products.
  * **Queue Monitoring** (`queue_monitoring.jsonl`): Information about queue lengths and wait times.
  * **Product Recognition** (`product_recognition.jsonl`): Data from the vision system that identifies products.
  * **Inventory Snapshots** (`inventory_snapshots.jsonl`): Periodic snapshots of the store's inventory.
  * **Product List** (`products_list.csv`): A catalog of all products, including their SKU, name, price, and weight.
  * **Customer Data** (`customer_data.csv`): A list of registered customers.
