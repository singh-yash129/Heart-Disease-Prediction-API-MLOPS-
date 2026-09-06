"""
generate_predictions.py — Deliverable 5
Generates 100-row random dataset and runs per-sample predictions
through the deployed API, logging each one to GCP Cloud Logging.
"""
import csv
import json
import os
import random
import sys
import time
from datetime import datetime, timezone

import requests

# ── Configuration ──────────────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8080")
ENDPOINT = f"{API_URL}/predict"
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

GENDERS = ["male", "female"]
random.seed(2024)


def random_patient():
    """Generate one random patient record within realistic clinical ranges."""
    return {
        "age":      random.randint(29, 77),
        "gender":   random.choice(GENDERS),
        "cp":       random.randint(0, 3),
        "trestbps": round(random.uniform(94, 200), 1),
        "chol":     round(random.uniform(126, 564), 1),
        "fbs":      random.randint(0, 1),
        "restecg":  random.randint(0, 2),
        "thalach":  round(random.uniform(71, 202), 1),
        "exang":    random.randint(0, 1),
        "oldpeak":  round(random.uniform(0.0, 6.2), 1),
        "slope":    random.randint(0, 2),
        "ca":       random.randint(0, 3),
        "thal":     random.randint(0, 3),
    }


def run():
    print(f"[START] Sending 100 per-sample predictions to {ENDPOINT}")
    print("   Each prediction is individually logged to GCP Cloud Logging.\n")

    results = []
    success = 0
    failed  = 0

    for i in range(1, 101):
        patient = random_patient()
        try:
            resp = requests.post(ENDPOINT, json=patient, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            result_row = {
                "sample_no":        i,
                "request_id":       data.get("request_id", ""),
                "timestamp":        data.get("timestamp", ""),
                "prediction":       data.get("prediction"),
                "prediction_label": data.get("prediction_label"),
                "probability":      data.get("probability"),
                **patient,
            }
            results.append(result_row)
            success += 1
            label = "[HD]" if data["prediction"] == 1 else "[OK]"
            print(f"  [{i:3d}] {label} {data['prediction_label']:20s} "
                  f"(p={data['probability']:.3f})  age={patient['age']} gender={patient['gender']}")

        except Exception as e:
            failed += 1
            print(f"  [{i:3d}] [ERR] ERROR: {e}")
            results.append({"sample_no": i, "error": str(e), **patient})

        # Small delay to avoid overwhelming local dev server
        time.sleep(0.05)

    # ── Save CSV ───────────────────────────────────────────────────────────────
    csv_path = os.path.join(REPORTS_DIR, "predictions_100_rows.csv")
    if results:
        fieldnames = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\nResults saved -> {csv_path}")

    print(f"\nSummary: {success} succeeded, {failed} failed out of 100")
    print("All predictions logged to GCP Cloud Logging via the API.")
    print("\nView logs at:")
    print("  https://console.cloud.google.com/logs/query;query=logName%3D%22heart-disease-api%22")
    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        API_URL  = sys.argv[1].rstrip("/")
        ENDPOINT = f"{API_URL}/predict"
    run()
