"""
predict.py
===========
Main inference entry point for the RTL Combinational Depth Predictor.

Three usage modes:

  1. CLI flags (recommended):
       python predict.py --file data/rtl/alu_8bit.v --signal result --module simple_alu

  2. Interactive prompt (run with no args):
       python predict.py

  3. Python API (import in scripts / notebooks):
       from predict import predict_depth
       info = predict_depth("my_design.v", "result", "simple_alu")
       print(info["predicted_depth"])

Options:
  --file   <path>    Path to Verilog (.v) file
  --signal <name>    Signal/net name to predict depth for
  --module <name>    Top module name (auto-detected if omitted)
  --clock  <ns>      Clock period in ns for timing check (default: 1.0)
  --model  <path>    Path to model .pkl (default: models/best_model.pkl)
"""

from __future__ import annotations

import sys
import os
import json
import time
import argparse
import warnings
from pathlib import Path

import numpy  as np
import pandas as pd
import joblib

warnings.filterwarnings("ignore")

# ── Project paths (src/ is one level below project root) ─────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]   # k:\project
MODEL_PATH   = PROJECT_ROOT / "models" / "best_model.pkl"
FEAT_PATH    = PROJECT_ROOT / "models" / "feature_columns.json"

# Ensure src/ is on path for feature_extraction import
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# Gate delay estimate: 0.1 ns per gate level (typical 28nm CMOS)
GATE_DELAY_NS = 0.1


def _load_model(model_path: str | Path = MODEL_PATH):
    if not Path(model_path).exists():
        raise FileNotFoundError(
            f"Model not found at {model_path}.\n"
            "Train it first:  python models/train.py"
        )
    model   = joblib.load(model_path)
    columns = []
    if FEAT_PATH.exists():
        info    = json.loads(FEAT_PATH.read_text())
        columns = info.get("columns", [])
    return model, columns


def _align_features(feature_dict: dict, columns: list[str]) -> pd.DataFrame:
    """Convert feature dict to a DataFrame aligned to training columns."""
    from feature_extraction import OPERATOR_COMPLEXITY  # src/feature_extraction.py

    # Remove non-feature keys
    exclude = {"signal_name", "module_name", "source_file"}
    row = {k: v for k, v in feature_dict.items() if k not in exclude}

    df = pd.DataFrame([row])
    # One-hot encode op_type
    if "op_type" in df.columns:
        df = pd.get_dummies(df, columns=["op_type"], dtype=int)

    # Align to training columns
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = 0
        df = df[columns]

    return df


def predict_depth(
    verilog_file:  str,
    signal_name:   str,
    top_module:    str | None = None,
    clock_period_ns: float = 1.0,
    model_path:    str | Path = MODEL_PATH,
) -> dict:
    """
    Predict the combinational depth of `signal_name` in `verilog_file`.

    Returns:
        {
          "signal":           str,
          "module":           str,
          "predicted_depth":  int,
          "estimated_delay_ns": float,
          "timing_ok":        bool,
          "features":         dict,
          "inference_ms":     float,
        }
    """
    # ── Validate file ─────────────────────────────────────────────────────────
    vf = Path(verilog_file)
    if not vf.exists():
        raise FileNotFoundError(f"Verilog file not found: {verilog_file}")

    # ── Import extractor ──────────────────────────────────────────────────────
    from feature_extraction import VerilogFeatureExtractor

    # ── Extract features ──────────────────────────────────────────────────────
    ext = VerilogFeatureExtractor(str(vf))

    if top_module is None:
        top_module = ext.get_top_module()

    t0    = time.perf_counter()
    feats = ext.extract_signal_features(signal_name)
    model, columns = _load_model(model_path)

    X    = _align_features(feats, columns)
    pred = float(model.predict(X)[0])
    depth = max(0, round(pred))
    inf_ms = (time.perf_counter() - t0) * 1000

    estimated_delay = depth * GATE_DELAY_NS
    timing_ok       = estimated_delay <= clock_period_ns

    return {
        "signal":             signal_name,
        "module":             top_module,
        "predicted_depth":    depth,
        "estimated_delay_ns": round(estimated_delay, 3),
        "timing_ok":          timing_ok,
        "clock_period_ns":    clock_period_ns,
        "features":           {k: v for k, v in feats.items()
                               if k not in ("signal_name", "module_name")},
        "inference_ms":       round(inf_ms, 2),
    }


def _print_result(result: dict):
    """Pretty-print prediction results."""
    print()
    print("+--------------------------------------------------+")
    print("|     RTL Combinational Depth Predictor Result     |")
    print("+--------------------------------------------------+")
    print(f"  Signal         : {result['signal']}")
    print(f"  Module         : {result['module']}")
    print(f"  Predicted Depth: {result['predicted_depth']} gate levels")
    print(f"  Est. Delay     : {result['estimated_delay_ns']} ns")
    print(f"  Clock Period   : {result['clock_period_ns']} ns")

    if result["timing_ok"]:
        print(f"  Timing Status  : [OK] OK ? no violation")
    else:
        slack = result["estimated_delay_ns"] - result["clock_period_ns"]
        print(f"  Timing Status  : [!]?  WARNING ? TIMING VIOLATION ({slack:.3f} ns over)")

    print(f"  Inference Time : {result['inference_ms']} ms")
    print()
    print("  Key Features Extracted:")
    f = result["features"]
    print(f"    Fan-in         : {f.get('fanin', '?')}")
    print(f"    Fan-out        : {f.get('fanout', '?')}")
    print(f"    Signal width   : {f.get('signal_width', '?')} bits")
    print(f"    Operator type  : {f.get('op_type', '?')}")
    print(f"    Nesting depth  : {f.get('nesting_depth', '?')}")
    print(f"    Has multiply   : {'Yes' if f.get('has_mul') else 'No'}")
    print()


def _interactive_mode():
    """Prompt user interactively for inputs."""
    print()
    print("  ?---------------------------------------------?")
    print("  |   RTL Combinational Depth Predictor v1.0    |")
    print("  |   Interactive Mode                          |")
    print("  ?---------------------------------------------?")
    print()

    vf = input("  📂 Verilog file path  : ").strip().strip('"')
    if not vf:
        print("  [ERR] No file provided.")
        return

    from feature_extraction import VerilogFeatureExtractor
    try:
        ext       = VerilogFeatureExtractor(vf)
        auto_mod  = ext.get_top_module()
    except Exception:
        auto_mod  = "unknown"

    signal = input("  🔎 Signal name        : ").strip()
    mod_in = input(f"  🏗️  Top module [{auto_mod}]  : ").strip()
    module = mod_in if mod_in else auto_mod

    clk_in = input("  ⏱️  Clock period (ns) [1.0]: ").strip()
    clock  = float(clk_in) if clk_in else 1.0

    print()
    print("  Predicting ?")
    result = predict_depth(vf, signal, module, clock)
    _print_result(result)


def main():
    parser = argparse.ArgumentParser(
        description="RTL Combinational Depth Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file",   "-f", help="Path to Verilog (.v) file")
    parser.add_argument("--signal", "-s", help="Signal name to analyze")
    parser.add_argument("--module", "-m", help="Top module name (auto-detected if omitted)")
    parser.add_argument("--clock",  "-c", type=float, default=1.0,
                        help="Clock period in ns (default: 1.0)")
    parser.add_argument("--model",        default=str(MODEL_PATH),
                        help="Path to model .pkl file")

    args = parser.parse_args()

    # Interactive mode if no flags given
    if not args.file or not args.signal:
        _interactive_mode()
        return

    try:
        result = predict_depth(
            verilog_file   = args.file,
            signal_name    = args.signal,
            top_module     = args.module,
            clock_period_ns= args.clock,
            model_path     = args.model,
        )
        _print_result(result)
    except FileNotFoundError as exc:
        print(f"\n[ERR] Error: {exc}\n")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERR] Prediction failed: {exc}\n")
        raise


if __name__ == "__main__":
    main()
