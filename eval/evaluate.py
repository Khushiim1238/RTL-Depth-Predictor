"""
evaluate.py
============
Evaluates the trained model on the held-out test set and generates plots.

Metrics reported:
  • MAE (Mean Absolute Error)
  • RMSE (Root Mean Squared Error)
  • Accuracy within +-1 depth  (primary hackathon metric)
  • Accuracy within +-2 depth
  • Inference time per sample

Plots saved to results/:
  • actual_vs_predicted.png   — scatter plot
  • feature_importance.png    — bar chart (tree-based models)
  • error_distribution.png    — histogram of prediction errors

Run from project root:
    python eval/evaluate.py
"""

from __future__ import annotations

import os
import sys
import json
import math
import warnings

import numpy  as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")            # non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics         import mean_absolute_error, mean_squared_error

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "dataset.csv"
MODELS_DIR   = PROJECT_ROOT / "models"
RESULTS_DIR  = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)

plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor":   "#16213e",
    "axes.edgecolor":   "#0f3460",
    "text.color":       "#eaeaea",
    "axes.labelcolor":  "#eaeaea",
    "xtick.color":      "#eaeaea",
    "ytick.color":      "#eaeaea",
    "grid.color":       "#0f3460",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "sans-serif",
})

ACCENT  = "#e94560"
ACCENT2 = "#0f3460"
GREEN   = "#06d6a0"
YELLOW  = "#ffd166"


def load_model_and_features() -> tuple:
    model_path = MODELS_DIR / "best_model.pkl"
    feat_path  = MODELS_DIR / "feature_columns.json"
    if not model_path.exists():
        sys.exit("[ERR] Model not found. Run: python models/train.py")
    model   = joblib.load(model_path)
    columns = []
    best_name = "Best Model"
    if feat_path.exists():
        info      = json.loads(feat_path.read_text())
        columns   = info.get("columns", [])
        best_name = info.get("best_model", "Best Model")
    return model, columns, best_name


def load_data(columns: list[str]) -> tuple:
    df = pd.read_csv(DATASET_PATH)
    df = df.dropna(subset=["actual_depth"])
    df["actual_depth"] = df["actual_depth"].astype(int)

    numeric = [
        "fanin", "fanout", "signal_width", "op_complexity",
        "nesting_depth", "operation_count",
        "has_mul", "has_add", "in_loop", "is_registered",
        "module_input_count", "conditional_mux_count",
    ]
    df_enc = pd.get_dummies(df[numeric + ["op_type"]],
                            columns=["op_type"], dtype=int)

    # Align columns to training feature set
    if columns:
        for col in columns:
            if col not in df_enc.columns:
                df_enc[col] = 0
        df_enc = df_enc[columns]

    X = df_enc
    y = df["actual_depth"]
    return X, y


def compute_metrics(y_true, y_pred) -> dict:
    err   = np.abs(y_true.values - y_pred)
    mae   = mean_absolute_error(y_true, y_pred)
    rmse  = math.sqrt(mean_squared_error(y_true, y_pred))
    acc1  = float(np.mean(err <= 1) * 100)
    acc2  = float(np.mean(err <= 2) * 100)
    return {
        "MAE":               round(mae, 3),
        "RMSE":              round(rmse, 3),
        "Accuracy_within_1": round(acc1, 1),
        "Accuracy_within_2": round(acc2, 1),
        "Max_error":         int(err.max()),
        "Median_error":      round(float(np.median(err)), 2),
    }


def plot_actual_vs_predicted(y_true, y_pred, model_name: str):
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    ax.scatter(y_true, y_pred, alpha=0.6, s=40,
               color=ACCENT, edgecolors="none", label="Predictions")

    lo, hi = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    ax.plot([lo, hi], [lo, hi], color=GREEN, lw=2, ls="--", label="Perfect fit")
    ax.fill_between([lo, hi], [lo-1, hi-1], [lo+1, hi+1],
                    color=GREEN, alpha=0.1, label="+-1 depth band")

    ax.set_xlabel("Actual Depth",    fontsize=12)
    ax.set_ylabel("Predicted Depth", fontsize=12)
    ax.set_title(f"Actual vs Predicted — {model_name}", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True)

    path = RESULTS_DIR / "actual_vs_predicted.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [CHART] Saved: {path}")


def plot_feature_importance(model, feature_cols: list[str]):
    """Plot feature importance for tree-based models."""
    raw = None

    # Unwrap Pipeline if needed
    est = model
    if hasattr(model, "named_steps"):
        est = model.named_steps.get("model", model)

    if hasattr(est, "feature_importances_"):
        raw = est.feature_importances_
    else:
        print("  [i]  Feature importance not available for this model type.")
        return

    imp  = pd.Series(raw, index=feature_cols).sort_values(ascending=True)
    top  = imp.tail(15)   # top 15

    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    bars = ax.barh(top.index, top.values, color=ACCENT, alpha=0.85)
    for bar in bars:
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.3f}", va="center", fontsize=8, color=YELLOW)

    ax.set_xlabel("Importance", fontsize=12)
    ax.set_title("Feature Importance (Top 15)", fontsize=14, fontweight="bold")
    ax.grid(True, axis="x")

    path = RESULTS_DIR / "feature_importance.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [CHART] Saved: {path}")


def plot_error_distribution(errors: np.ndarray):
    fig, ax = plt.subplots(figsize=(8, 5), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    bins = range(0, int(errors.max()) + 2)
    ax.hist(errors, bins=bins, color=ACCENT2, edgecolor=ACCENT, alpha=0.9)

    within1 = (errors <= 1).sum()
    ax.axvline(1.5, color=GREEN, ls="--", lw=2, label=f"+-1 boundary ({within1} samples)")

    ax.set_xlabel("Absolute Error (|predicted - actual|)", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    ax.set_title("Prediction Error Distribution", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(True, axis="y")

    path = RESULTS_DIR / "error_distribution.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [CHART] Saved: {path}")


def main():
    print("=" * 60)
    print("  RTL Depth Predictor ? Model Evaluation")
    print("=" * 60)

    model, feature_cols, best_name = load_model_and_features()
    X, y = load_data(feature_cols)

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nEvaluating on {len(X_test)} test samples ?")

    y_pred = np.round(model.predict(X_test)).astype(int)
    errors = np.abs(y_test.values - y_pred)

    metrics = compute_metrics(y_test, y_pred)

    # ── Print metrics ─────────────────────────────────────────────────────────
    print(f"\n  Model: {best_name}")
    print("  " + "-" * 40)
    for k, v in metrics.items():
        print(f"  {k:<25} {v}")
    print("  " + "-" * 40)

    # Hackathon target check
    if metrics["Accuracy_within_1"] >= 75:
        print(f"\n  [OK] +-1 Accuracy: {metrics['Accuracy_within_1']}% ? TARGET MET (>=75%)")
    else:
        print(f"\n  [!]  +-1 Accuracy: {metrics['Accuracy_within_1']}% ? below 75% target")

    # ── Save metrics ──────────────────────────────────────────────────────────
    eval_path = RESULTS_DIR / "evaluation_metrics.json"
    with open(eval_path, "w") as fh:
        json.dump({best_name: metrics}, fh, indent=2)
    print(f"\n  Saved: {eval_path}")

    # ── Plots ─────────────────────────────────────────────────────────────────
    print("\n  Generating plots ?")
    plot_actual_vs_predicted(y_test, y_pred, best_name)
    plot_feature_importance(model, feature_cols or [f"f{i}" for i in range(X_test.shape[1])])
    plot_error_distribution(errors)

    print("\n[OK] Evaluation complete! Plots saved to results/\n")
    return metrics


if __name__ == "__main__":
    main()