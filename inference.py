"""
inference.py
=============
Python API wrapper for the RTL Combinational Depth Predictor.

Import this module in notebooks, other scripts, or testing:

    from inference import predict_depth, batch_predict

Examples:
    # Single signal
    result = predict_depth("data/rtl/local/simple_alu_8bit.v", "result", "simple_alu_8bit")
    print(result["predicted_depth"])

    # Batch prediction
    signals = [
        ("data/rtl/local/ripple_carry_adder_8bit.v", "sum",   "ripple_carry_adder_8bit"),
        ("data/rtl/local/array_multiplier_8bit.v",   "product","array_multiplier_8bit"),
    ]
    results = batch_predict(signals)
    for r in results:
        print(f"{r['signal']}: depth={r['predicted_depth']}")
"""

from __future__ import annotations
import sys
import os
from pathlib import Path

# Ensure project root is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import predict_depth  # re-export


def batch_predict(
    signals: list[tuple[str, str, str | None]],
    clock_period_ns: float = 1.0,
) -> list[dict]:
    """
    Predict combinational depth for multiple signals.

    Args:
        signals: List of (verilog_file, signal_name, top_module) tuples.
                 top_module can be None for auto-detection.
        clock_period_ns: Clock period for timing check (default 1.0 ns = 1 GHz).

    Returns:
        List of result dicts (same format as predict_depth).
    """
    results = []
    for item in signals:
        vf, sig = item[0], item[1]
        mod     = item[2] if len(item) > 2 else None
        try:
            r = predict_depth(vf, sig, mod, clock_period_ns)
            results.append(r)
        except Exception as exc:
            results.append({
                "signal": sig,
                "module": mod or "unknown",
                "error":  str(exc),
                "predicted_depth": -1,
                "timing_ok": None,
            })
    return results


def get_model_info() -> dict:
    """Return metadata about the currently loaded model."""
    import json
    feat_path = Path(__file__).resolve().parent / "models" / "feature_columns.json"
    if feat_path.exists():
        return json.loads(feat_path.read_text())
    return {"columns": [], "best_model": "unknown"}


__all__ = ["predict_depth", "batch_predict", "get_model_info"]