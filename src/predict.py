"""
predict.py — Prediction logic (loaded once at startup by app.py)
"""
import os
import joblib
import numpy as np
import pandas as pd

MODEL_DIR    = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH   = os.path.join(MODEL_DIR, "heart_disease_model.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")

# Gender encoding must mirror train.py's pd.factorize order
# pd.factorize on ['male','female',...] → male=0, female=1
GENDER_MAP = {"male": 0, "female": 1}


def load_model():
    """Load trained model and feature column list."""
    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(COLUMNS_PATH)
    return model, feature_cols


def preprocess_input(data: dict, feature_cols: list) -> pd.DataFrame:
    """Convert API input dict to model-ready DataFrame."""
    row = dict(data)
    # Encode gender
    gender_str = str(row.get("gender", "male")).lower()
    row["gender"] = GENDER_MAP.get(gender_str, 0)
    df = pd.DataFrame([row])
    # Ensure column order and types match training
    df = df[feature_cols].astype(float)
    return df


def predict_single(model, feature_cols: list, data: dict) -> dict:
    """Run prediction for a single sample."""
    X = preprocess_input(data, feature_cols)
    pred_label = model.predict(X)[0]           # 'yes' or 'no'
    prob_array = model.predict_proba(X)[0]      # [p_no, p_yes]
    # Map class order
    classes = list(model.classes_)
    yes_idx = classes.index("yes") if "yes" in classes else 1
    probability = float(prob_array[yes_idx])

    return {
        "prediction": 1 if pred_label == "yes" else 0,
        "prediction_label": "Heart Disease" if pred_label == "yes" else "No Heart Disease",
        "probability": round(probability, 4),
        "raw_label": str(pred_label),
    }
