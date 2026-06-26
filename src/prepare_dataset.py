"""
prepare_dataset.py
==================
One-stop script that:
  1. Generates 56 local RTL designs (if data/rtl_designs/local/ is empty)
  2. Extracts per-signal features from every .v file in data/rtl_designs/
  3. Writes data/dataset.csv (ready for model training)

Usage:
    python src/prepare_dataset.py [--rtl-dir PATH] [--out PATH]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Ensure src/ is importable
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))          # for backward-compat imports

RTL_DIR  = PROJECT_ROOT / "data" / "rtl_designs"
OUT_CSV  = PROJECT_ROOT / "data" / "dataset.csv"


def _ensure_local_designs():
    """Generate local RTL designs if the directory is empty."""
    local_dir = RTL_DIR / "local"
    if local_dir.exists() and any(local_dir.glob("*.v")):
        print(f"  Local RTL already present ({len(list(local_dir.glob('*.v')))} files)")
        return

    print("  Generating local RTL designs ...")
    gen_script = PROJECT_ROOT / "data" / "scripts" / "generate_rtl_local.py"
    if gen_script.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("gen", gen_script)
        mod  = importlib.util.module_from_spec(spec)
        # Patch OUT_DIR to point to the new location
        import types
        mod.__dict__["OUT_DIR"] = str(local_dir)
        spec.loader.exec_module(mod)
    else:
        print("  [!] generate_rtl_local.py not found — skipping local generation.")


def main():
    parser = argparse.ArgumentParser(description="Prepare RTL dataset")
    parser.add_argument("--rtl-dir", default=str(RTL_DIR),
                        help=f"Root RTL directory (default: {RTL_DIR})")
    parser.add_argument("--out", default=str(OUT_CSV),
                        help=f"Output CSV path (default: {OUT_CSV})")
    parser.add_argument("--no-generate", action="store_true",
                        help="Skip local design generation")
    args = parser.parse_args()

    rtl_dir = Path(args.rtl_dir)
    out_csv = Path(args.out)

    print("=" * 60)
    print("  RTL Dataset Preparation")
    print("=" * 60)

    # Step 1 — ensure RTL files exist
    if not args.no_generate:
        _ensure_local_designs()

    v_files = list(rtl_dir.rglob("*.v"))
    if not v_files:
        print(f"\n[!] No .v files found under {rtl_dir}")
        print("    Download RTL:  python data/scripts/download_rtl.py")
        sys.exit(1)

    print(f"\n  Found {len(v_files)} Verilog files under {rtl_dir}")

    # Step 2 — extract features
    from feature_extraction import extract_features
    rows = extract_features(str(rtl_dir), str(out_csv))

    print(f"\n[DONE] Dataset ready: {out_csv}")
    print(f"       Rows: {len(rows)}  |  Next: python src/train_models.py")


if __name__ == "__main__":
    main()
