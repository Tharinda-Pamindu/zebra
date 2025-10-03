import os
import subprocess
import time
import shutil

# --- Configuration ---
# Define paths relative to the script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, '..', '..', 'src')
DATA_DIR = os.path.join(BASE_DIR, '..', '..', 'data')
EVIDENCE_OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'output', 'test')

STREAM_SERVER_SCRIPT = os.path.join(DATA_DIR, 'streaming-server', 'stream_server.py')
EVENT_PROCESSOR_SCRIPT = os.path.join(SRC_DIR, 'main.py')
DASHBOARD_REQUIREMENTS = os.path.join(SRC_DIR, 'dashboard', 'requirements.txt')

OUTPUT_EVENTS_FILE = os.path.join(BASE_DIR, '..', '..', 'events.jsonl')
FINAL_EVENTS_FILE = os.path.join(EVIDENCE_OUTPUT_DIR, 'events.jsonl')

# --- Main Automation Logic ---
def run_demo():
    """
    Orchestrates the entire demo, from setup to generating output.
    """
    print("--- Starting Project Sentinel Demo ---")

    # 1. Ensure the output directory exists
    os.makedirs(EVIDENCE_OUTPUT_DIR, exist_ok=True)
    print(f"Ensured output directory exists: {EVIDENCE_OUTPUT_DIR}")

    # 2. Install dependencies
    print("Installing dashboard dependencies...")
    try:
        subprocess.run(['pip', 'install', '-r', DASHBOARD_REQUIREMENTS], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return

    # 3. Start the streaming server in the background
    print(f"Starting the stream server from: {STREAM_SERVER_SCRIPT}")
    stream_server_process = subprocess.Popen(['python', STREAM_SERVER_SCRIPT, '--speed', '100', '--loop'])
    time.sleep(2)  # Give the server a moment to start

    # 4. Start the event detection script
    print(f"Starting the event detection script: {EVENT_PROCESSOR_SCRIPT}")
    event_processor_process = subprocess.Popen(['python', EVENT_PROCESSOR_SCRIPT])

    # 5. Let it run for a while to collect events
    print("Running event detection for 30 seconds...")
    time.sleep(30)

    # 6. Terminate the processes
    print("Stopping event detection and stream server...")
    event_processor_process.terminate()
    stream_server_process.terminate()

    # Wait for processes to close to avoid race conditions
    event_processor_process.wait()
    stream_server_process.wait()
    print("Processes stopped.")

    # 7. Copy the output file to the evidence directory
    if os.path.exists(OUTPUT_EVENTS_FILE):
        print(f"Copying '{OUTPUT_EVENTS_FILE}' to '{FINAL_EVENTS_FILE}'")
        shutil.copy(OUTPUT_EVENTS_FILE, FINAL_EVENTS_FILE)
        print("Output file copied successfully.")
    else:
        print(f"Error: Output file '{OUTPUT_EVENTS_FILE}' not found.")

    print("--- Demo Finished ---")

if __name__ == "__main__":
    run_demo()