"""
drift_detection.py — Input Drift Detection using Evidently (Deliverable 7)
Compares training data distribution vs 100-row generated prediction data.
"""
import os
import json
import joblib
import pandas as pd
import numpy as np

MODEL_DIR    = os.path.join(os.path.dirname(__file__), "..", "model")
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


def run_drift_detection(current_data_path: str = None):
    try:
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset
        from evidently.metrics import DatasetDriftMetric
    except ImportError:
        try:
            from evidently import Report
            from evidently.metric_preset import DataDriftPreset
            from evidently.metrics import DatasetDriftMetric
        except ImportError:
            from evidently.legacy.report import Report
            from evidently.legacy.metric_preset import DataDriftPreset
            from evidently.legacy.metrics import DatasetDriftMetric

    # ── Load reference (training) data ────────────────────────────────────────
    train_data = joblib.load(os.path.join(MODEL_DIR, "train_data.pkl"))
    feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_columns.pkl"))

    # Use only feature columns (drop target if present)
    ref_cols = [c for c in feature_cols if c in train_data.columns]
    reference = train_data[ref_cols].reset_index(drop=True)

    # ── Load current (inference) data ─────────────────────────────────────────
    if current_data_path is None:
        current_data_path = os.path.join(REPORTS_DIR, "predictions_100_rows.csv")

    current_raw = pd.read_csv(current_data_path)

    # Extract feature columns from prediction CSV
    feature_subset = [c for c in ref_cols if c in current_raw.columns]
    current = current_raw[feature_subset].reset_index(drop=True)

    # Align dtypes & handle gender string if present
    if "gender" in current.columns and current["gender"].dtype == object:
        current["gender"] = current["gender"].map({"male": 0, "female": 1, "Male": 0, "Female": 1}).fillna(0)

    for col in feature_subset:
        current[col]   = pd.to_numeric(current[col],   errors="coerce")
        reference[col] = pd.to_numeric(reference[col], errors="coerce")

    print(f"📊 Reference data shape : {reference.shape}")
    print(f"📊 Current data shape   : {current.shape}")

    # ── Run Evidently Drift Report ────────────────────────────────────────────
    report = Report(metrics=[
        DataDriftPreset(),
        DatasetDriftMetric(),
    ])
    report.run(reference_data=reference[feature_subset],
               current_data=current[feature_subset])

    # Save HTML report
    html_path = os.path.join(REPORTS_DIR, "drift_report.html")
    report.save_html(html_path)
    print(f"💾 Drift HTML report saved → {html_path}")

    # ── Extract JSON summary ──────────────────────────────────────────────────
    result_json = report.as_dict()
    drift_results = []

    for metric in result_json.get("metrics", []):
        if metric.get("metric") == "DatasetDriftMetric":
            r = metric["result"]
            dataset_drift = r.get("dataset_drift", False)
            drift_share   = r.get("share_of_drifted_columns", 0)
            print(f"\n{'⚠️ DRIFT DETECTED' if dataset_drift else '✅ NO DRIFT'}")
            print(f"   Drifted columns share: {drift_share:.2%}")

        if metric.get("metric") == "DataDriftTable":
            for col, info in metric["result"].get("drift_by_columns", {}).items():
                drifted = info.get("drift_detected", False)
                p_val   = info.get("p_value", None)
                method  = info.get("stattest_name", "")
                drift_results.append({
                    "feature":        col,
                    "drift_detected": drifted,
                    "p_value":        round(p_val, 4) if p_val else None,
                    "test_method":    method,
                })

    if drift_results:
        drift_df = pd.DataFrame(drift_results).sort_values("drift_detected", ascending=False)
        print("\n📋 Per-Feature Drift Summary:")
        print(drift_df.to_string(index=False))

        # Save JSON summary
        json_path = os.path.join(REPORTS_DIR, "drift_summary.json")
        drift_df.to_json(json_path, orient="records", indent=2)
        print(f"💾 Drift JSON summary saved → {json_path}")

    print(f"\n✅ Drift detection complete. Open {html_path} for the full report.")
    return drift_results


if __name__ == "__main__":
    run_drift_detection()
