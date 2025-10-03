import json
import os
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# --- Configuration ---
# Construct an absolute path to the events file to avoid pathing issues
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVENTS_FILE = os.path.join(BASE_DIR, '..', '..', 'events.jsonl')

def get_events():
    """Reads events from the JSONL file."""
    events = []
    try:
        with open(EVENTS_FILE, 'r') as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    # Log or handle corrupted lines if necessary
                    pass
    except FileNotFoundError:
        # Handle case where the file doesn't exist yet
        print(f"File not found: {EVENTS_FILE}")
        pass
    return events

@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html', events=get_events())

@app.route('/data')
def data():
    """Provides the event data as JSON."""
    return jsonify(get_events())

if __name__ == '__main__':
    app.run(debug=True, port=5001)