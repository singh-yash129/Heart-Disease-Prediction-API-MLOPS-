"""
run_drift_detection.py — Deliverable 7 runner script
Usage: python scripts/run_drift_detection.py [path/to/predictions.csv]
"""
import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.drift_detection import run_drift_detection

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_drift_detection(current_data_path=csv_path)
