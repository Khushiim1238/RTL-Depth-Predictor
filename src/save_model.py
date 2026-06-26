"""
save_model.py
=============
Utility to export / re-save the trained model in different formats.

Operations:
  1. Verify best_model.pkl exists and loads cleanly
  2. Print model type + feature column list
  3. Optionally export to ONNX (if skl2onnx is installed)
  4. Write a human-readable model_info.txt summary

Usage:
    python src/save_model.py                    # verify + print info
    python src/save_model.py --export-onnx      # also export to ONNX
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR   = PROJECT_ROOT / "models"
MODEL_PATH   = MODELS_DIR / "best_model.pkl"
FEAT_PATH    = MODELS_DIR / "feature_columns.json"
INFO_PATH    = MODELS_DIR / "model_info.txt"


def load_and_verify() -> tuple:
    """Load model + feature list, do a sanity prediction."""
    if not MODEL_PATH.exists():
        sys.exit(f"[!] Model not found: {MODEL_PATH}\n    Run: python src/train_models.py first")

    model = joblib.load(MODEL_PATH)

    columns, best_name = [], "unknown"
    if FEAT_PATH.exists():
        info      = json.loads(FEAT_PATH.read_text())
        columns   = info.get("columns", [])
        best_name = info.get("best_model", "unknown")

    return model, columns, best_name


def print_model_info(model, columns: list[str], best_name: str):
    print(f"  Model type   : {type(model).__name__}")
    print(f"  Best model   : {best_name}")
    print(f"  Feature count: {len(columns)}")
    print(f"  Features     :")
    for i, c in enumerate(columns, 1):
        print(f"    {i:>2}. {c}")


def write_info_file(model, columns: list[str], best_name: str):
    lines = [
        "RTL Combinational Depth Predictor - Model Info",
        "=" * 50,
        f"Model type    : {type(model).__name__}",
        f"Best model    : {best_name}",
        f"Feature count : {len(columns)}",
        "",
        "Feature columns (in order):",
    ]
    for i, c in enumerate(columns, 1):
        lines.append(f"  {i:>2}. {c}")

    INFO_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Saved model info -> {INFO_PATH}")


def export_onnx(model, columns: list[str], best_name: str):
    """Export model to ONNX format (requires skl2onnx)."""
    try:
        from skl2onnx import convert_sklearn
        from skl2onnx.common.data_types import FloatTensorType
    except ImportError:
        print("  [!] skl2onnx not installed. Run:  pip install skl2onnx")
        return

    initial_type = [("float_input", FloatTensorType([None, len(columns)]))]
    try:
        onnx_model = convert_sklearn(model, initial_types=initial_type)
        onnx_path  = MODELS_DIR / "best_model.onnx"
        with open(onnx_path, "wb") as f:
            f.write(onnx_model.SerializeToString())
        print(f"  Exported ONNX -> {onnx_path}")
    except Exception as exc:
        print(f"  [!] ONNX export failed: {exc}")


def sanity_check(model, columns: list[str]):
    """Run a dummy prediction to confirm model is loadable."""
    if not columns:
        print("  [!] No feature columns found — skipping sanity check")
        return
    X = np.zeros((1, len(columns)))
    pred = model.predict(X)[0]
    print(f"  Sanity check  : dummy input -> predicted depth = {round(pred)}")


def main():
    parser = argparse.ArgumentParser(description="Save / export trained RTL depth model")
    parser.add_argument("--export-onnx", action="store_true",
                        help="Also export model to ONNX format")
    args = parser.parse_args()

    print("=" * 60)
    print("  RTL Depth Predictor - Model Save Utility")
    print("=" * 60)

    model, columns, best_name = load_and_verify()

    print(f"\n  Loaded: {MODEL_PATH}")
    print_model_info(model, columns, best_name)
    sanity_check(model, columns)
    write_info_file(model, columns, best_name)

    if args.export_onnx:
        export_onnx(model, columns, best_name)

    print("\n[DONE] Model verified and info saved.")


if __name__ == "__main__":
    main()
