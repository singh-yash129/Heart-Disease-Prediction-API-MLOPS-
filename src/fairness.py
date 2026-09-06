"""
fairness.py — Fairlearn Fairness Testing (Deliverable 3)
Sensitive attribute: age (binned into groups)
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


def bin_age(age_series: pd.Series) -> pd.Series:
    """Bin age into clinical categories."""
    bins   = [0, 40, 50, 60, 70, 200]
    labels = ["<40", "40-49", "50-59", "60-69", "70+"]
    return pd.cut(age_series, bins=bins, labels=labels, right=False)


def run_fairness_analysis():
    import warnings
    warnings.filterwarnings("ignore")
    from fairlearn.metrics import MetricFrame, selection_rate
    from sklearn.metrics import accuracy_score, precision_score, recall_score

    # ── Load model & data ─────────────────────────────────────────────────────
    model        = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(COLUMNS_PATH)

    df = pd.read_csv(DATA_PATH)
    df["gender"] = pd.factorize(df["gender"])[0]
    df = df.dropna()

    X = df[feature_cols].astype(float)
    y_true_labels = df["target"]                  # 'yes'/'no'
    y_true_bin    = (y_true_labels == "yes").astype(int)

    # Predictions
    y_pred_labels = model.predict(X)
    y_pred_bin    = (pd.Series(y_pred_labels) == "yes").astype(int).values

    # Sensitive feature: age group
    age_groups = bin_age(df["age"])

    # ── MetricFrame ───────────────────────────────────────────────────────────
    metrics_dict = {
        "accuracy":       accuracy_score,
        "precision":      lambda yt, yp: precision_score(yt, yp, zero_division=0),
        "recall":         lambda yt, yp: recall_score(yt, yp, zero_division=0),
        "selection_rate": selection_rate,
    }

    mf = MetricFrame(
        metrics=metrics_dict,
        y_true=y_true_bin,
        y_pred=y_pred_bin,
        sensitive_features=age_groups,
    )

    print("\n📊 Overall Metrics:")
    print(mf.overall)
    print("\n📊 Metrics by Age Group:")
    print(mf.by_group)

    # ── Disparity analysis ────────────────────────────────────────────────────
    group_df    = mf.by_group.reset_index()
    group_df.columns = ["age_group"] + list(metrics_dict.keys())
    max_acc_gap = group_df["accuracy"].max() - group_df["accuracy"].min()
    max_rec_gap = group_df["recall"].max()   - group_df["recall"].min()

    print(f"\n⚠️  Max accuracy gap across age groups: {max_acc_gap:.4f}")
    print(f"⚠️  Max recall gap across age groups:   {max_rec_gap:.4f}")

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Fairlearn — Fairness Analysis by Age Group", fontsize=14, fontweight="bold")

    colors = ["#2a9d8f", "#e76f51", "#457b9d", "#e9c46a", "#264653"]
    for ax, metric in zip(axes, ["accuracy", "recall"]):
        vals = group_df[metric].values
        bars = ax.bar(group_df["age_group"].astype(str), vals,
                      color=colors[:len(vals)], edgecolor="white")
        ax.axhline(float(mf.overall[metric]), color="red", linestyle="--",
                   linewidth=1.5, label=f"Overall ({float(mf.overall[metric]):.3f})")
        ax.set_ylim(0, 1.1)
        ax.set_title(f"{metric.capitalize()} by Age Group")
        ax.set_xlabel("Age Group")
        ax.set_ylabel(metric.capitalize())
        ax.legend(fontsize=9)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{val:.3f}", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    plot_path = os.path.join(REPORTS_DIR, "fairness_by_age.png")
    plt.savefig(plot_path, dpi=150)
    plt.close()
    print(f"\n💾 Fairness plot saved → {plot_path}")

    # ── Write report ──────────────────────────────────────────────────────────
    report_path = os.path.join(REPORTS_DIR, "fairness_report.md")
    with open(report_path, "w") as f:
        f.write("# Deliverable 3: Fairness Testing with Fairlearn\n\n")
        f.write("## Sensitive Attribute: Age (Binned)\n\n")
        f.write("Age was binned into five clinical groups: `<40`, `40-49`, `50-59`, `60-69`, `70+`.\n\n")
        f.write("## Overall Model Metrics\n\n")
        f.write("| Metric | Value |\n|--------|-------|\n")
        for k, v in mf.overall.items():
            f.write(f"| {k} | {float(v):.4f} |\n")
        f.write("\n## Metrics by Age Group\n\n")
        try:
            f.write(group_df.to_markdown(index=False))
        except Exception:
            cols = list(group_df.columns)
            f.write("| " + " | ".join(str(c) for c in cols) + " |\n")
            f.write("| " + " | ".join(["---"] * len(cols)) + " |\n")
            for _, r in group_df.iterrows():
                f.write("| " + " | ".join(f"{val:.4f}" if isinstance(val, (float, np.floating)) else str(val) for val in r) + " |\n")
        f.write("\n\n## Disparity Analysis\n\n")
        f.write(f"- **Max accuracy gap** across age groups: `{max_acc_gap:.4f}`\n")
        f.write(f"- **Max recall gap** across age groups: `{max_rec_gap:.4f}`\n\n")
        if max_acc_gap > 0.1:
            f.write("> ⚠️ **Significant accuracy disparity detected** (>10%). ")
            f.write("The model may be less reliable for certain age cohorts.\n\n")
        else:
            f.write("> ✅ **No significant accuracy disparity** detected (<10% gap across age groups).\n\n")
        f.write("## Interpretation\n\n")
        f.write("Fairness testing with `fairlearn.metrics.MetricFrame` reveals how model performance ")
        f.write("varies across age groups. Elevated recall gaps may indicate the model misses ")
        f.write("heart disease cases in specific age bands, which is clinically significant.\n\n")
        f.write("![Fairness by Age](fairness_by_age.png)\n")

    print(f"✅ Fairness report saved → {report_path}")
    return mf


if __name__ == "__main__":
    run_fairness_analysis()
