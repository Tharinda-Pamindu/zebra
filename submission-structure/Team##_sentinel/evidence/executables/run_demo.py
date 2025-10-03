#!/usr/bin/env python3
"""Automation script for Project Sentinel event detection.

This script:
1. Verifies Python dependencies (uses only standard library)
2. Processes input data and generates events.jsonl
3. Produces output in evidence/output/ directories
"""

import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Verify Python 3.9+ is available."""
    if sys.version_info < (3, 9):
        sys.stderr.write("Error: Python 3.9 or higher is required.\n")
        sys.exit(1)
    print(f"✓ Using Python {sys.version_info.major}.{sys.version_info.minor}")


def run_processing(data_dir: Path, output_dir: Path):
    """Run the event detection processing.
    
    Args:
        data_dir: Path to input data directory
        output_dir: Path to output directory
    """
    src_dir = Path(__file__).parent.parent.parent / "src"
    main_script = src_dir / "main.py"
    output_file = output_dir / "events.jsonl"
    
    print(f"\nProcessing data from: {data_dir}")
    print(f"Output will be written to: {output_file}")
    
    # Run the main processing script
    result = subprocess.run(
        [sys.executable, str(main_script), str(data_dir), str(output_file)],
        cwd=str(src_dir),
        capture_output=False
    )
    
    if result.returncode != 0:
        sys.stderr.write(f"Error: Processing failed with exit code {result.returncode}\n")
        sys.exit(result.returncode)
    
    print(f"✓ Successfully generated: {output_file}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Project Sentinel - Event Detection System")
    print("=" * 60)
    
    # Check Python version
    check_python_version()
    
    # Determine base paths
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent.parent  # Team##_sentinel directory
    evidence_dir = base_dir / "evidence"
    
    # Default to sample data if no arguments provided
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])
        if len(sys.argv) > 2:
            output_dir = Path(sys.argv[2])
        else:
            output_dir = evidence_dir / "output" / "test"
    else:
        # Use default paths relative to repository root
        # From executables: ../../../../data/input
        repo_root = base_dir.parent.parent
        data_dir = repo_root / "data" / "input"
        output_dir = evidence_dir / "output" / "test"
    
    if not data_dir.exists():
        sys.stderr.write(f"Error: Data directory not found: {data_dir}\n")
        sys.stderr.write("Usage: python run_demo.py [data_dir] [output_dir]\n")
        sys.exit(1)
    
    # Process the data
    run_processing(data_dir, output_dir)
    
    print("\n" + "=" * 60)
    print("Processing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
