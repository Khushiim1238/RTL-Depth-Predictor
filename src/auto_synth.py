"""
auto_synth.py
=============
Automates Yosys synthesis on every Verilog design in data/rtl_designs/
and saves a timing report for each to data/synthesis_reports/.

If Yosys is not installed, falls back to the analytical depth labeller
in src/feature_extraction.py so the pipeline still works end-to-end.

Usage:
    python src/auto_synth.py [--yosys-path /path/to/yosys]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT     = Path(__file__).resolve().parents[1]
RTL_DIR          = PROJECT_ROOT / "data" / "rtl_designs"
REPORTS_DIR      = PROJECT_ROOT / "data" / "synthesis_reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Yosys synth script template
YOSYS_SCRIPT = """\
read_verilog {v_file}
synth -top {module} -flatten
abc -fast
tee -o {rpt_file} stat
"""


def find_yosys() -> str | None:
    """Return path to yosys executable if available, else None."""
    return shutil.which("yosys")


def run_yosys(v_file: Path, module: str, yosys_bin: str) -> Path | None:
    """
    Run Yosys synthesis and save report.
    Returns path to .rpt file on success, None on failure.
    """
    rpt_file = REPORTS_DIR / (v_file.stem + ".rpt")
    script   = YOSYS_SCRIPT.format(
        v_file=str(v_file).replace("\\", "/"),
        module=module,
        rpt_file=str(rpt_file).replace("\\", "/"),
    )

    try:
        result = subprocess.run(
            [yosys_bin, "-p", script],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            _write_structured_report(rpt_file, v_file.stem, result.stdout)
            return rpt_file
        else:
            print(f"  [!] Yosys error for {v_file.name}: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print(f"  [!] Timeout for {v_file.name}")
    except Exception as exc:
        print(f"  [!] Failed {v_file.name}: {exc}")
    return None


def _write_structured_report(rpt_file: Path, module: str, yosys_stdout: str):
    """Write a structured key-value report from Yosys stdout."""
    # Try to extract longest path from Yosys stat output
    depth = 0
    m = re.search(r"Longest\s+path[^:]*:\s*(\d+)", yosys_stdout, re.IGNORECASE)
    if m:
        depth = int(m.group(1))

    with open(rpt_file, "w", encoding="utf-8") as fh:
        fh.write(f"module: {module}\n")
        fh.write(f"depth: {depth}\n")
        fh.write("\n--- Yosys Output ---\n")
        fh.write(yosys_stdout)


def _get_top_module(v_file: Path) -> str:
    """Extract the first module name from a Verilog file."""
    try:
        text = v_file.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"\bmodule\s+(\w+)", text)
        return m.group(1) if m else v_file.stem
    except Exception:
        return v_file.stem


def analytical_fallback(v_file: Path):
    """
    Generate a report using analytical depth formulas when Yosys is absent.
    Imports from src/feature_extraction.py.
    """
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from feature_extraction import VerilogFeatureExtractor

    ext    = VerilogFeatureExtractor(str(v_file))
    sigs   = ext.get_combinational_signals()
    module = ext.get_top_module()

    rpt_file = REPORTS_DIR / (v_file.stem + ".rpt")
    lines = [f"module: {module}\n"]

    for sig in sigs[:5]:  # first 5 combinational outputs
        name = sig["name"]
        if ext._is_registered(name):
            continue
        feats = ext.extract_signal_features(name)
        depth = ext.compute_depth(feats)
        lines.append(f"signal: {name}\n")
        lines.append(f"width: {sig['width']}\n")
        lines.append(f"depth: {depth}\n")
        lines.append("\n")

    rpt_file.write_text("".join(lines), encoding="utf-8")
    return rpt_file


def main():
    parser = argparse.ArgumentParser(description="Automated RTL Synthesis with Yosys")
    parser.add_argument("--yosys-path", default=None,
                        help="Path to yosys binary (auto-detected if omitted)")
    parser.add_argument("--force-analytical", action="store_true",
                        help="Skip Yosys even if installed; use analytical labels")
    args = parser.parse_args()

    v_files = sorted(RTL_DIR.rglob("*.v"))
    if not v_files:
        print(f"[!] No .v files found in {RTL_DIR}")
        print("    Run: python src/prepare_dataset.py  first")
        return

    print(f"Found {len(v_files)} Verilog files in {RTL_DIR}")

    yosys_bin = None
    if not args.force_analytical:
        yosys_bin = args.yosys_path or find_yosys()

    if yosys_bin:
        print(f"Using Yosys at: {yosys_bin}\n")
        ok, fail = 0, 0
        for vf in v_files:
            module = _get_top_module(vf)
            print(f"  Synthesising {vf.name} (module: {module}) ...", end=" ")
            rpt = run_yosys(vf, module, yosys_bin)
            if rpt:
                print("OK")
                ok += 1
            else:
                print("FAILED")
                fail += 1
        print(f"\n[DONE] {ok} synthesised, {fail} failed. Reports -> {REPORTS_DIR}")
    else:
        print("Yosys not found. Using analytical depth labels as fallback.\n")
        for vf in v_files:
            print(f"  Labelling {vf.name} ...", end=" ")
            rpt = analytical_fallback(vf)
            print(f"-> {rpt.name}")
        print(f"\n[DONE] Analytical reports -> {REPORTS_DIR}")


if __name__ == "__main__":
    main()
