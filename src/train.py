"""
train.py — Heart Disease Model Training Script
Extracted from: HeartDiseaseTrainingAndPrediction.ipynb
Model: LogisticRegression with RandomizedSearchCV (same as reference notebook)
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn import metrics

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "data.csv")
MODEL_DIR   = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH  = os.path.join(MODEL_DIR, "heart_disease_model.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")
TRAIN_DATA_PATH = os.path.join(MODEL_DIR, "train_data.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)


def train():
    print("📊 Loading dataset...")
    df = pd.read_csv(DATA_PATH)

    # ── Preprocessing (mirrors notebook exactly) ──────────────────────────────
    # Encode gender: factorize → male=0, female=1 (as in notebook)
    df["gender"] = pd.factorize(df["gender"])[0]

    # Drop rows with NaN (notebook uses dropna)
    cleaned_df = df.dropna()
    print(f"   Rows after cleaning: {cleaned_df.shape[0]}")

    # Features & target — drop sno (index column) and target
    feature_cols = [c for c in cleaned_df.columns if c not in ["target", "sno"]]
    X = cleaned_df[feature_cols]
    y = cleaned_df["target"]   # 'yes' / 'no'

    # ── Train / Test split ────────────────────────────────────────────────────
    np.random.seed(42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"   Train: {len(X_train)}, Test: {len(X_test)}")

    # ── Hyperparameter search (same grid as notebook) ─────────────────────────
    log_reg_grid = {
        "C":      np.logspace(-4, 4, 20),
        "solver": ["liblinear"],
    }
    rs_log_reg = RandomizedSearchCV(
        LogisticRegression(max_iter=1000),
        param_distributions=log_reg_grid,
        cv=5,
        n_iter=20,
        verbose=1,
        random_state=42,
    )
    print("🔍 Running RandomizedSearchCV...")
    rs_log_reg.fit(X_train, y_train)
    print(f"   Best params: {rs_log_reg.best_params_}")

    # ── Evaluate ──────────────────────────────────────────────────────────────
    test_score = rs_log_reg.score(X_test, y_test)
    print(f"✅ Test accuracy: {test_score:.4f}")

    y_pred = rs_log_reg.predict(X_test)
    print("\n📋 Classification Report:")
    print(metrics.classification_report(y_test, y_pred))

    # ── Persist ───────────────────────────────────────────────────────────────
    joblib.dump(rs_log_reg, MODEL_PATH)
    joblib.dump(feature_cols, COLUMNS_PATH)

    # Save training split for drift detection baseline
    train_df = X_train.copy()
    train_df["target"] = y_train.values
    joblib.dump(train_df, TRAIN_DATA_PATH)

    print(f"\n💾 Model saved  → {MODEL_PATH}")
    print(f"💾 Columns saved → {COLUMNS_PATH}")
    print(f"💾 Train data saved → {TRAIN_DATA_PATH}")
    return rs_log_reg, feature_cols


if __name__ == "__main__":
    train()
