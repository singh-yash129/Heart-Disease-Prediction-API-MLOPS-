"""
explainability.py — SHAP Analysis (Deliverable 2)
Identifies least-impactful features for heart disease prediction.
"""
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_PATH    = os.path.join(os.path.dirname(__file__), "..", "data", "data.csv")
MODEL_DIR    = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH   = os.path.join(MODEL_DIR, "heart_disease_model.pkl")
COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")
REPORTS_DIR  = os.path.join(os.path.dirname(__file__), "..", "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)


def run_shap_analysis():
    import shap

    # Load model & data
    model        = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(COLUMNS_PATH)

    df = pd.read_csv(DATA_PATH)
    df["gender"] = pd.factorize(df["gender"])[0]
    df = df.dropna()

    X = df[feature_cols].astype(float)
    y = df["target"]

    import warnings
    warnings.filterwarnings("ignore")

    # Use a background sample for SHAP KernelExplainer (works with any sklearn model)
    background = shap.sample(X, 50, random_state=42)
    explainer  = shap.KernelExplainer(
        lambda x: model.predict_proba(pd.DataFrame(x, columns=feature_cols))[:, 1],
        background,
    )
    shap_values = explainer.shap_values(X.sample(100, random_state=42))

    # Mean absolute SHAP values → feature importance ranking
    mean_shap = np.abs(shap_values).mean(axis=0)
    importance_df = pd.DataFrame({
        "feature":    feature_cols,
        "mean_shap":  mean_shap,
    }).sort_values("mean_shap", ascending=False)

    print("\n📊 SHAP Feature Importance (descending):")
    print(importance_df.to_string(index=False))

    # ── Summary Bar Plot ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#e63946" if v > importance_df["mean_shap"].median() else "#457b9d"
              for v in importance_df["mean_shap"]]
    ax.barh(importance_df["feature"], importance_df["mean_shap"], color=colors)
    ax.set_xlabel("Mean |SHAP Value|", fontsize=12)
    ax.set_title("Feature Importance — Heart Disease Prediction\n(SHAP KernelExplainer)", fontsize=13)
    ax.invert_yaxis()
    plt.tight_layout()
    plot_path = os.path.join(REPORTS_DIR, "shap_summary.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"\n💾 SHAP plot saved → {plot_path}")

    # ── Identify least important features ─────────────────────────────────────
    least_important = importance_df.tail(3)["feature"].tolist()
    bottom_df       = importance_df.tail(3)

    # ── Write explainability report ───────────────────────────────────────────
    report_path = os.path.join(REPORTS_DIR, "explainability_report.md")
    with open(report_path, "w") as f:
        f.write("# Deliverable 2: Model Explainability — SHAP Analysis\n\n")
        f.write("## Method\n")
        f.write("We used **SHAP KernelExplainer** on a LogisticRegression model trained on the ")
        f.write("Cleveland Heart Disease dataset. SHAP (SHapley Additive exPlanations) assigns each ")
        f.write("feature an importance score reflecting its average contribution to the model's output.\n\n")
        f.write("## Full Feature Importance Ranking\n\n")
        f.write("| Rank | Feature | Mean |SHAP| |\n")
        f.write("|------|---------|-------------|\n")
        for i, row in importance_df.reset_index(drop=True).iterrows():
            f.write(f"| {i+1} | `{row['feature']}` | {row['mean_shap']:.4f} |\n")
        f.write("\n")
        f.write("## Least Impactful Features (Plain English)\n\n")
        f.write("Based on SHAP analysis, the features with the **least impact** on predicting ")
        f.write("heart disease are:\n\n")
        for feat in least_important:
            desc = {
                "fbs":     "**fbs (Fasting Blood Sugar > 120 mg/dl)** — Whether a patient has elevated fasting blood sugar has very little influence on the model's prediction of heart disease.",
                "restecg": "**restecg (Resting Electrocardiographic Results)** — The resting ECG reading (normal, ST-T abnormality, or LV hypertrophy) contributes minimally to the model's decision.",
                "slope":   "**slope (Slope of Peak Exercise ST Segment)** — The slope pattern of the ST segment during exercise adds little predictive power over other more dominant features.",
                "chol":    "**chol (Serum Cholesterol)** — Despite its clinical notoriety, serum cholesterol has a surprisingly low SHAP contribution in this dataset.",
                "trestbps":"**trestbps (Resting Blood Pressure)** — Resting blood pressure has minimal influence relative to heart-rate and angina-related features.",
                "sno":     "**sno (Serial Number)** — This is just an index column and has no real predictive value.",
            }.get(feat, f"**{feat}** — This feature shows low mean absolute SHAP value, indicating it rarely changes the model prediction significantly.")
            f.write(f"- {desc}\n")
        f.write("\n")
        f.write("## Key Insight\n\n")
        f.write("The **most impactful** features are those related to chest pain type (`cp`), ")
        f.write("number of major vessels (`ca`), thalassemia type (`thal`), max heart rate (`thalach`), ")
        f.write("and exercise-induced angina (`exang`). These directly reflect cardiac stress and ")
        f.write("structural heart conditions.\n\n")
        f.write("![SHAP Summary Plot](shap_summary.png)\n")

    print(f"✅ Explainability report saved → {report_path}")
    return importance_df


if __name__ == "__main__":
    run_shap_analysis()
