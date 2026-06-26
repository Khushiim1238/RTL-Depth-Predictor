"""
train.py
=========
Trains 5 ML models on the RTL combinational depth dataset and saves the best.

Models compared:
  1. Linear Regression    (baseline)
  2. Decision Tree
  3. Random Forest
  4. XGBoost
  5. MLP Neural Network

Outputs:
  models/best_model.pkl          – joblib-serialised best model
  models/feature_columns.json    – feature column list (required for inference)
  results/model_comparison.json  – metrics for all models

Run from project root:
    python models/train.py
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
import warnings

import numpy  as np
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing   import StandardScaler
from sklearn.linear_model    import LinearRegression
from sklearn.tree            import DecisionTreeRegressor
from sklearn.ensemble        import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network  import MLPRegressor
from sklearn.metrics         import mean_absolute_error, mean_squared_error
from sklearn.pipeline        import Pipeline

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[!]  xgboost not installed ? using GradientBoostingRegressor as substitute.")

warnings.filterwarnings("ignore")

# ── Paths ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "dataset.csv"
MODELS_DIR   = PROJECT_ROOT / "models"
RESULTS_DIR  = PROJECT_ROOT / "results"

MODELS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# ── Feature columns ───────────────────────────────────────────────────────────
NUMERIC_FEATURES = [
    "fanin", "fanout", "signal_width", "op_complexity",
    "nesting_depth", "operation_count",
    "has_mul", "has_add", "in_loop", "is_registered",
    "module_input_count", "conditional_mux_count",
]
CATEGORICAL_FEATURES = ["op_type"]
TARGET = "actual_depth"


def load_and_prepare(csv_path: Path) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Load dataset, one-hot encode categoricals, return X, y, feature_cols."""
    df = pd.read_csv(csv_path)

    if len(df) < 10:
        sys.exit(
            f"❌ Dataset has only {len(df)} rows — too few to train.\n"
            "   Please run the data pipeline first:\n"
            "     python data/scripts/generate_rtl_local.py\n"
            "     python features/extractor.py"
        )

    print(f"Loaded dataset: {len(df)} rows, {df.shape[1]} columns")
    print(f"Depth distribution:\n{df[TARGET].describe().to_string()}\n")

    # Drop rows with missing depth
    df = df.dropna(subset=[TARGET])
    df[TARGET] = df[TARGET].astype(int)

    # One-hot encode op_type
    df_enc = pd.get_dummies(df[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
                            columns=CATEGORICAL_FEATURES, dtype=int)

    feature_cols = list(df_enc.columns)
    X = df_enc
    y = df[TARGET]

    return X, y, feature_cols


def evaluate(model, X_test, y_test) -> dict:
    """Compute all evaluation metrics."""
    t0    = time.perf_counter()
    y_pred = np.round(model.predict(X_test)).astype(int)
    inf_ms = (time.perf_counter() - t0) * 1000

    mae   = mean_absolute_error(y_test, y_pred)
    rmse  = math.sqrt(mean_squared_error(y_test, y_pred))
    acc1  = float(np.mean(np.abs(y_test.values - y_pred) <= 1) * 100)
    acc2  = float(np.mean(np.abs(y_test.values - y_pred) <= 2) * 100)

    return {
        "MAE":               round(mae, 3),
        "RMSE":              round(rmse, 3),
        "Accuracy_within_1": round(acc1, 1),
        "Accuracy_within_2": round(acc2, 1),
        "Inference_ms":      round(inf_ms, 2),
    }


def build_models() -> dict:
    """Build all model definitions."""
    xgb_model = (
        xgb.XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, verbosity=0
        )
        if XGBOOST_AVAILABLE
        else GradientBoostingRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            random_state=42
        )
    )
    xgb_name = "XGBoost" if XGBOOST_AVAILABLE else "GradientBoosting"

    return {
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  LinearRegression()),
        ]),
        "Decision Tree": DecisionTreeRegressor(max_depth=12, random_state=42),
        "Random Forest": RandomForestRegressor(
            n_estimators=200, max_depth=15, min_samples_leaf=2,
            random_state=42, n_jobs=-1
        ),
        xgb_name: xgb_model,
        "MLP Neural Network": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation="relu", solver="adam",
                max_iter=1000, random_state=42,
                early_stopping=True, validation_fraction=0.1,
            )),
        ]),
    }


def main():
    print("=" * 60)
    print("  RTL Depth Predictor ? Model Training")
    print("=" * 60)

    # ── Load data ─────────────────────────────────────────────────────────────
    X, y, feature_cols = load_and_prepare(DATASET_PATH)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows\n")

    # ── Train & evaluate ──────────────────────────────────────────────────────
    models   = build_models()
    results  = {}
    trained  = {}

    for name, model in models.items():
        print(f"  Training: {name} ?")
        t0 = time.perf_counter()
        model.fit(X_train, y_train)
        train_s = time.perf_counter() - t0

        metrics = evaluate(model, X_test, y_test)
        metrics["Train_time_s"] = round(train_s, 2)

        # 5-fold CV MAE
        cv = cross_val_score(model, X, y, cv=5,
                             scoring="neg_mean_absolute_error", n_jobs=-1)
        metrics["CV_MAE_5fold"] = round(-cv.mean(), 3)

        results[name]  = metrics
        trained[name]  = model
        print(f"    MAE={metrics['MAE']:.2f}  RMSE={metrics['RMSE']:.2f}"
              f"  ±1 acc={metrics['Accuracy_within_1']:.1f}%"
              f"  CV-MAE={metrics['CV_MAE_5fold']:.2f}")

    # ── Print comparison table ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  {'Model':<25}  {'MAE':>6}  {'RMSE':>6}  {'+-1 Acc%':>8}  {'+-2 Acc%':>8}  {'CV-MAE':>7}")
    print("  " + "-" * 65)
    for name, m in results.items():
        print(f"  {name:<25}  {m['MAE']:>6}  {m['RMSE']:>6}  "
              f"{m['Accuracy_within_1']:>8}  {m['Accuracy_within_2']:>8}  "
              f"{m['CV_MAE_5fold']:>7}")
    print("=" * 70)

    # ── Select best model (lowest CV MAE) ────────────────────────────────────
    best_name = min(results, key=lambda n: results[n]["CV_MAE_5fold"])
    best_model = trained[best_name]
    print(f"\n[BEST] Best model: {best_name}  (CV-MAE = {results[best_name]['CV_MAE_5fold']})")

    # ── Save artifacts ────────────────────────────────────────────────────────
    model_path = MODELS_DIR / "best_model.pkl"
    joblib.dump(best_model, model_path)
    print(f"   Saved: {model_path}")

    feat_path = MODELS_DIR / "feature_columns.json"
    with open(feat_path, "w") as fh:
        json.dump({"columns": feature_cols, "best_model": best_name}, fh, indent=2)
    print(f"   Saved: {feat_path}")

    res_path = RESULTS_DIR / "model_comparison.json"
    with open(res_path, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"   Saved: {res_path}")

    print("\n[DONE] Training complete!\n")
    return results, best_name


if __name__ == "__main__":
    main()