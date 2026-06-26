"""Fix all non-ASCII characters in Python source files for Windows cp1252 compatibility."""
import os

FILES = [
    "predict.py",
    "eval/evaluate.py",
    "data/scripts/download_rtl.py",
    "models/train.py",
    "features/extractor.py",
]

for path in FILES:
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    fixed = []
    changed = 0
    for line in lines:
        # Only process print() lines — they're the ones that go to stdout
        if "print(" in line and any(ord(c) > 127 for c in line):
            new_line = ""
            for ch in line:
                if ord(ch) < 128:
                    new_line += ch
                else:
                    # Replace known symbols
                    replacements = {
                        "\u2554": "+", "\u2550": "-", "\u2557": "+",
                        "\u2551": "|", "\u255a": "+", "\u255d": "+",
                        "\u2502": "|", "\u2500": "-",
                        "\u2713": "[OK]",  "\u2714": "[OK]",
                        "\u2717": "[X]",   "\u274c": "[ERR]",
                        "\u2705": "[OK]",  "\u26a0": "[!]",
                        "\u2139": "[i]",   "\u2192": "->",
                        "\u2265": ">=",    "\u2264": "<=",
                        "\u00b1": "+-",    "\u2260": "!=",
                        "\U0001f3c6": "[BEST]",
                        "\U0001f4ca": "[CHART]",
                        "\U0001f4c2": "[FOLDER]",
                        "\U0001f50e": "[SEARCH]",
                        "\U0001f3d7": "[BUILD]",
                        "\U0001f4c4": "[FILE]",
                        "\u23f1": "[TIME]",
                    }
                    new_line += replacements.get(ch, "?")
                    changed += 1
            fixed.append(new_line)
        else:
            fixed.append(line)

    if changed > 0:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(fixed)
        print(f"  Fixed {changed} chars in {path}")
    else:
        print(f"  OK (no changes): {path}")

print("\nAll files cleaned.")
