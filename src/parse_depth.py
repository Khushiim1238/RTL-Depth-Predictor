"""
synthesis_parser.py
====================
Parses structured synthesis report (.rpt) files produced by Yosys or our
analytical label generator.

Supported report formats:

  Format A (key-value):
    signal: sum
    width: 8
    depth: 9

  Format B (inline label - legacy):
    depth: 9

  Format C (Yosys stat output - partial support):
    Longest path: 9
"""

from __future__ import annotations
import re
from pathlib import Path


def parse_report(report_path: str) -> dict | None:
    """
    Parse a synthesis report file and return a dict with at least 'depth'.
    Returns None if depth cannot be found.
    """
    try:
        text = Path(report_path).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return None

    result: dict = {}

    # Signal name
    m = re.search(r"^signal\s*:\s*(\w+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        result["signal"] = m.group(1)

    # Bit-width
    m = re.search(r"^width\s*:\s*(\d+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        result["width"] = int(m.group(1))

    # Module
    m = re.search(r"^module\s*:\s*(\w+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        result["module"] = m.group(1)

    # Depth — try all formats
    depth = None

    # Format A / B: "depth: N"
    m = re.search(r"^depth\s*:\s*(\d+)", text, re.MULTILINE | re.IGNORECASE)
    if m:
        depth = int(m.group(1))

    # Format C: "Longest path: N"  or "Longest path length: N"
    if depth is None:
        m = re.search(r"longest\s+path[^:]*:\s*(\d+)", text, re.IGNORECASE)
        if m:
            depth = int(m.group(1))

    if depth is None:
        return None

    result["depth"] = depth
    return result


def parse_reports_dir(reports_dir: str) -> dict[str, int]:
    """
    Parse all .rpt files in `reports_dir`.
    Returns dict mapping signal name (or filename stem) → depth.
    """
    mapping: dict[str, int] = {}
    for rpt in Path(reports_dir).glob("*.rpt"):
        info = parse_report(str(rpt))
        if info and "depth" in info:
            key = info.get("signal", rpt.stem)
            mapping[key] = info["depth"]
    return mapping