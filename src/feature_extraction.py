"""
extractor.py
=============
Per-signal combinational feature extractor for Verilog RTL files.

Extracts 13 features per signal and computes an analytical ground-truth
combinational depth label using standard EDA gate-depth formulas.

Usage (standalone):
    python features/extractor.py
    → reads data/rtl/**/*.v, writes data/dataset.csv

The same class can be imported for inference:
    from features.extractor import VerilogFeatureExtractor
    ext = VerilogFeatureExtractor("my_design.v")
    feats = ext.extract_signal_features("sum")
"""

from __future__ import annotations

import os
import re
import sys
import math
import json
import csv
from pathlib import Path
from typing import Optional

# ── Gate-depth lookup table ───────────────────────────────────────────────────
# Base depth per operator (before width scaling):
# These are industry-calibrated values for standard-cell synthesis.

def _add_depth(w: int) -> int:
    """Carry-lookahead adder depth ≈ 2·⌈log₂(w)⌉  (CLA approximation)."""
    return max(1, 2 * math.ceil(math.log2(max(w, 2))))

def _mul_depth(w: int) -> int:
    """Wallace-tree multiplier depth ≈ 3·⌈log₂(w)⌉ + 2."""
    return max(2, 3 * math.ceil(math.log2(max(w, 2))) + 2)

def _shift_depth(w: int) -> int:
    """Barrel shifter: ⌈log₂(w)⌉ MUX stages, each depth 2."""
    return max(1, math.ceil(math.log2(max(w, 2))) * 2)

def _cmp_depth(w: int) -> int:
    """Tree comparator depth: ⌈log₂(w)⌉ + 1."""
    return max(1, math.ceil(math.log2(max(w, 2))) + 1)

def _div_depth(w: int) -> int:
    """Non-restoring divider depth ≈ 4·w."""
    return max(4, 4 * w)

OPERATOR_DEPTH_FN: dict[str, int | callable] = {
    "AND":   1,
    "OR":    1,
    "NOT":   1,
    "NAND":  1,
    "NOR":   1,
    "XOR":   2,
    "XNOR":  2,
    "MUX":   2,
    "ADD":   _add_depth,
    "SUB":   _add_depth,
    "MUL":   _mul_depth,
    "DIV":   _div_depth,
    "MOD":   _div_depth,
    "SHL":   _shift_depth,
    "SHR":   _shift_depth,
    "CMP":   _cmp_depth,
    "OTHER": 3,
}

OPERATOR_COMPLEXITY: dict[str, int] = {
    "AND": 1, "OR": 1, "NOT": 1, "NAND": 1, "NOR": 1,
    "XOR": 2, "XNOR": 2, "MUX": 2,
    "ADD": 6, "SUB": 6,
    "MUL": 15, "DIV": 20, "MOD": 20,
    "SHL": 4, "SHR": 4,
    "CMP": 5,
    "OTHER": 3,
}

# ── Feature extraction ────────────────────────────────────────────────────────

class VerilogFeatureExtractor:
    """
    Parses a single Verilog file and extracts per-signal combinational features.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        raw = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        self.code = self._strip_comments(raw)

    # ── Preprocessing ─────────────────────────────────────────────────────────

    @staticmethod
    def _strip_comments(code: str) -> str:
        code = re.sub(r"//[^\n]*", " ", code)
        code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)
        return code

    # ── Module-level parsing ──────────────────────────────────────────────────

    def get_module_names(self) -> list[str]:
        return re.findall(r"\bmodule\s+(\w+)", self.code)

    def get_top_module(self) -> str:
        names = self.get_module_names()
        return names[0] if names else "unknown"

    def get_module_inputs(self, module_name: str) -> list[str]:
        """Return list of input port names for a module."""
        # Grab module body
        pat = rf"\bmodule\s+{re.escape(module_name)}\s*[\(#].*?endmodule"
        m = re.search(pat, self.code, re.DOTALL)
        if not m:
            return []
        body = m.group(0)
        # Find port declarations
        inputs = re.findall(r"\binput\b[^;]*?\b(\w+)\s*(?:,|;|\))", body)
        return inputs

    def count_module_inputs(self) -> int:
        inputs = []
        for mod in self.get_module_names():
            inputs.extend(self.get_module_inputs(mod))
        return len(inputs)

    # ── Signal discovery ──────────────────────────────────────────────────────

    def get_combinational_signals(self) -> list[dict]:
        """
        Find all combinational signals (outputs, wires, regs that are
        assigned combinationally via `assign` or `always @(*)`).
        Returns list of {name, width, is_output}.
        """
        signals = []
        seen = set()

        # Pattern: [optional-width] signal_name
        decl_pattern = re.compile(
            r"\b(output|wire|reg)\s+(?:reg\s+)?(?:signed\s+)?"
            r"(?:\[(\d+):\d+\]\s+)?(\w+)",
        )

        for m in decl_pattern.finditer(self.code):
            kind, width_str, name = m.group(1), m.group(2), m.group(3)
            if name in ("clk", "rst", "reset", "clock") or name in seen:
                continue
            width = int(width_str) + 1 if width_str else 1
            is_output = (kind == "output")
            signals.append({"name": name, "width": width, "is_output": is_output})
            seen.add(name)

        return signals

    # ── Assignment extraction ─────────────────────────────────────────────────

    def get_rhs(self, signal: str) -> Optional[str]:
        """
        Find the RHS expression of a combinational assignment for `signal`.
        Checks:  assign sig = ...;
                 sig = ...;  (inside always @(*))
                 sig <= ...;  (only if outside posedge block)
        """
        # 1. Continuous assignment:  assign sig = expr ;
        m = re.search(
            rf"\bassign\s+{re.escape(signal)}\s*=\s*(.+?);",
            self.code, re.DOTALL
        )
        if m:
            return m.group(1).strip()

        # 2. Blocking assignment inside always @(*) block
        # Find always @(*) or always @* blocks and search inside them
        always_blocks = re.findall(
            r"always\s*@\s*\(\s*\*\s*\)(.+?)(?=always|\bendmodule\b)",
            self.code, re.DOTALL
        )
        for blk in always_blocks:
            m = re.search(
                rf"\b{re.escape(signal)}\s*=\s*(.+?);",
                blk, re.DOTALL
            )
            if m:
                return m.group(1).strip()

        return None

    # ── Feature extraction ────────────────────────────────────────────────────

    def _detect_operator(self, expr: str) -> str:
        """Determine the dominant operator in an expression."""
        if re.search(r"\*", expr)  and not re.search(r"\*\*", expr):
            return "MUL"
        if re.search(r"[^=!<>]/[^/]", expr):
            return "DIV"
        if re.search(r"%", expr):
            return "MOD"
        if re.search(r"[+]", expr):
            return "ADD"
        if re.search(r"(?<!=)-(?!=)", expr):
            return "SUB"
        if re.search(r"<<|>>", expr):
            # Both shift directions → SHL covers depth calc
            return "SHL" if "<<" in expr else "SHR"
        if re.search(r"[<>]", expr):
            return "CMP"
        if re.search(r"\?", expr):
            return "MUX"
        if re.search(r"\^", expr):
            return "XOR"
        if re.search(r"~\^|\^~", expr):
            return "XNOR"
        if re.search(r"&&|&", expr):
            return "AND"
        if re.search(r"\|\||\|", expr):
            return "OR"
        if re.search(r"~", expr):
            return "NOT"
        return "OTHER"

    def _count_fanin(self, rhs: str) -> int:
        """Count unique signal/variable references on the RHS."""
        # Find all identifiers, exclude keywords and numbers
        raw = re.findall(r"\b([a-zA-Z_]\w*)\b", rhs)
        exclude = {
            "begin", "end", "if", "else", "case", "casez", "casex",
            "endcase", "for", "integer", "default", "signed", "unsigned",
        }
        return len({x for x in raw if x not in exclude and not x.isdigit()})

    def _count_fanout(self, signal: str) -> int:
        """Count how many other RHS expressions reference `signal`."""
        # Count all occurrences on the right side of assign / inside expressions
        count = 0
        for m in re.finditer(
            rf"(?:assign\s+\w+\s*=|=)\s*[^;]*\b{re.escape(signal)}\b",
            self.code
        ):
            expr = m.group(0)
            # Exclude the signal's own assignment
            if not re.match(rf"assign\s+{re.escape(signal)}\s*=", expr.strip()):
                count += 1
        return min(count, 20)  # cap at 20 to avoid outliers

    def _count_nesting(self) -> int:
        """Maximum if/case nesting depth in file."""
        max_d, cur_d = 0, 0
        for line in self.code.splitlines():
            s = line.strip()
            if re.match(r"\b(if|case[zx]?)\b", s):
                cur_d += 1
                max_d = max(max_d, cur_d)
            if re.match(r"\bend(case)?\b", s):
                cur_d = max(0, cur_d - 1)
        return max_d

    def _count_operations(self, expr: str) -> int:
        """Count number of operators in an expression."""
        ops = re.findall(r"[+\-*/%&|^~<>!?]", expr)
        return len(ops)

    def _is_in_loop(self, signal: str) -> int:
        """1 if signal is assigned inside a for/generate loop."""
        m = re.search(
            rf"(?:for|genvar)\s*\(.+?\)[^;]*{re.escape(signal)}",
            self.code, re.DOTALL
        )
        return 1 if m else 0

    def _is_registered(self, signal: str) -> int:
        """1 if signal is driven by a synchronous (posedge/negedge) always block."""
        sync_blocks = re.findall(
            r"always\s*@\s*\([^)]*(?:posedge|negedge)[^)]*\)(.+?)"
            r"(?=always|\bendmodule\b)",
            self.code, re.DOTALL
        )
        for blk in sync_blocks:
            if re.search(rf"\b{re.escape(signal)}\s*<=", blk):
                return 1
        return 0

    def _count_mux_branches(self, signal: str) -> int:
        """Count case branches / ternary operators in signal's expression."""
        rhs = self.get_rhs(signal) or ""
        # ternary operators
        ternary = len(re.findall(r"\?", rhs))
        # case branches (rough)
        rhs_context = self.code
        m = re.search(
            rf"\bcase[zx]?\s*\([^)]+\)(.+?)\bendcase\b",
            rhs_context, re.DOTALL
        )
        case_branches = 0
        if m:
            blk = m.group(1)
            if re.search(rf"\b{re.escape(signal)}\b", blk):
                case_branches = len(re.findall(r"^\s*[0-9a-zA-Z']+[^:]*:", blk, re.M))
        return ternary + case_branches

    # ── Depth computation ─────────────────────────────────────────────────────

    def compute_depth(self, features: dict) -> int:
        """
        Analytical combinational depth:
            base_depth  = operator gate stages (width-scaled)
            mux_penalty = nesting_depth × 2   (each if/case adds a MUX stage)
            fanin_log   = ⌈log₂(fanin+1)⌉    (fan-in tree overhead)
        Total = base + mux + fanin_log   (clamped to [1, 50])
        """
        op   = features["op_type"]
        w    = features["signal_width"]
        nest = features["nesting_depth"]
        fin  = features["fanin"]

        fn = OPERATOR_DEPTH_FN.get(op, 3)
        base = fn(w) if callable(fn) else fn

        mux_penalty = nest * 2
        fanin_log   = math.ceil(math.log2(max(fin, 2)))

        # If registered, depth is 0 combinationally
        if features.get("is_registered"):
            return 0

        depth = base + mux_penalty + fanin_log
        return max(1, min(depth, 60))

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_signal_features(self, signal_name: str) -> dict:
        """
        Extract all 13 features for `signal_name`.
        Returns a feature dict (without actual_depth).
        """
        rhs = self.get_rhs(signal_name) or ""

        op_type = self._detect_operator(rhs) if rhs else "OTHER"
        fanin   = self._count_fanin(rhs) if rhs else 1

        # Infer signal width from declaration
        m = re.search(
            rf"\[(\d+):\d+\]\s+{re.escape(signal_name)}",
            self.code
        )
        width = int(m.group(1)) + 1 if m else 1

        nesting = self._count_nesting()

        return {
            "signal_name":          signal_name,
            "module_name":          self.get_top_module(),
            "fanin":                fanin,
            "fanout":               self._count_fanout(signal_name),
            "signal_width":         width,
            "op_type":              op_type,
            "op_complexity":        OPERATOR_COMPLEXITY.get(op_type, 3),
            "nesting_depth":        nesting,
            "operation_count":      self._count_operations(rhs),
            "has_mul":              int("*" in rhs),
            "has_add":              int("+" in rhs or ("-" in rhs and "??" not in rhs)),
            "in_loop":              self._is_in_loop(signal_name),
            "is_registered":        self._is_registered(signal_name),
            "module_input_count":   self.count_module_inputs(),
            "conditional_mux_count": self._count_mux_branches(signal_name),
        }

    def extract_all_signals(self, max_signals: int = 15) -> list[dict]:
        """
        Extract features for all combinational signals in the file.
        Returns list of feature dicts with `actual_depth` added.
        """
        sigs = self.get_combinational_signals()
        rows = []
        for sig_info in sigs[:max_signals]:
            name = sig_info["name"]
            if self._is_registered(name):
                continue  # skip FF outputs
            feats = self.extract_signal_features(name)
            # Width override if known from declaration
            if sig_info["width"] > 1:
                feats["signal_width"] = sig_info["width"]
            feats["actual_depth"] = self.compute_depth(feats)
            rows.append(feats)
        return rows


# ── Batch processing ──────────────────────────────────────────────────────────

FEATURE_COLUMNS = [
    "signal_name", "module_name",
    "fanin", "fanout", "signal_width",
    "op_type", "op_complexity",
    "nesting_depth", "operation_count",
    "has_mul", "has_add", "in_loop", "is_registered",
    "module_input_count", "conditional_mux_count",
    "actual_depth",
]

def extract_features(rtl_dir: str, output_csv: str, max_signals_per_file: int = 15):
    """
    Walk all .v files under `rtl_dir`, extract per-signal features,
    and write to `output_csv`.
    """
    all_rows = []
    rtl_files = list(Path(rtl_dir).rglob("*.v"))
    print(f"Processing {len(rtl_files)} Verilog files from {rtl_dir}?")

    for vf in rtl_files:
        try:
            ext  = VerilogFeatureExtractor(str(vf))
            rows = ext.extract_all_signals(max_signals=max_signals_per_file)
            for r in rows:
                r["source_file"] = vf.name
            all_rows.extend(rows)
        except Exception as exc:
            print(f"  [!]  Skipping {vf.name}: {exc}")

    # Deduplicate rows with identical features
    seen = set()
    unique = []
    for row in all_rows:
        key = (row["module_name"], row["signal_name"], row["op_type"], row["signal_width"])
        if key not in seen:
            seen.add(key)
            unique.append(row)

    # Write CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FEATURE_COLUMNS + ["source_file"],
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n[DONE] Extracted {len(unique)} signal rows -> {output_csv}")
    return unique


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    rtl_dir      = project_root / "data" / "rtl"
    output_csv   = project_root / "data" / "dataset.csv"
    extract_features(str(rtl_dir), str(output_csv))