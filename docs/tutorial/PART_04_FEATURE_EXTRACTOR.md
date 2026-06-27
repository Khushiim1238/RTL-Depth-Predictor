# Part 4 — Building the Feature Extractor (`features/extractor.py`)

> **[<< Part 3: Requirements](./PART_03_REQUIREMENTS.md)** | **[Next: Dataset Prep >>](./PART_05_DATASET_PREP.md)**

---

## What You Will Learn

- Why this file is the most important in the entire project
- How to parse Verilog source code using regular expressions
- What each of the 13 features means and how it is calculated
- How the analytical depth formula works
- How to build a class that can be used both standalone AND imported

---

## Why This File Is the Heart of the Project

`features/extractor.py` does something that NO library does for you — it **converts raw Verilog text into a numerical feature vector** that a machine learning model can understand.

Every other script in the project is just wiring. This one does the real intellectual work.

> **No Verilog parser library is used.** This is intentional. Using regex makes the code dependency-free, portable, and fast (O(n) over the text length).

---

## Section 1 — The Gate-Depth Lookup Table (Lines 1–82)

This is written **before** the class. These are **module-level functions and dictionaries**.

### Step 1: Write the depth formula functions

Open `features/extractor.py`. The file starts with these functions:

```python
import math

def _add_depth(w: int) -> int:
    """Carry-lookahead adder depth = 2 * ceil(log2(w))."""
    return max(1, 2 * math.ceil(math.log2(max(w, 2))))

def _mul_depth(w: int) -> int:
    """Wallace-tree multiplier depth = 3 * ceil(log2(w)) + 2."""
    return max(2, 3 * math.ceil(math.log2(max(w, 2))) + 2)

def _shift_depth(w: int) -> int:
    """Barrel shifter: ceil(log2(w)) MUX stages, each 2 gates deep."""
    return max(1, math.ceil(math.log2(max(w, 2))) * 2)

def _cmp_depth(w: int) -> int:
    """Tree comparator: ceil(log2(w)) + 1."""
    return max(1, math.ceil(math.log2(max(w, 2))) + 1)

def _div_depth(w: int) -> int:
    """Non-restoring divider: very deep, ~4 * w."""
    return max(4, 4 * w)
```

**Why `max(w, 2)` everywhere?** `log2(0)` and `log2(1)` are problematic. `max(w, 2)` ensures we never take log2 of a number <= 1, which would give 0 or negative results.

**Why `max(1, ...)` as outer wrapper?** A depth of 0 would mean "no gates at all", which is only valid for registered signals. Even a wire buffer costs 1 gate level.

### Step 2: Write the operator lookup dictionaries

```python
OPERATOR_DEPTH_FN = {
    "AND":   1,          # Single gate
    "OR":    1,          # Single gate
    "NOT":   1,          # Single gate (inverter)
    "NAND":  1,
    "NOR":   1,
    "XOR":   2,          # Two-level implementation
    "XNOR":  2,
    "MUX":   2,          # 2:1 MUX = 2 gate levels
    "ADD":   _add_depth, # Function — depends on bit width!
    "SUB":   _add_depth, # Subtraction uses adder circuit
    "MUL":   _mul_depth,
    "DIV":   _div_depth,
    "MOD":   _div_depth,
    "SHL":   _shift_depth,
    "SHR":   _shift_depth,
    "CMP":   _cmp_depth,
    "OTHER": 3,          # Default for unknown operators
}

OPERATOR_COMPLEXITY = {
    "AND": 1, "OR": 1, "NOT": 1, "NAND": 1, "NOR": 1,
    "XOR": 2, "XNOR": 2, "MUX": 2,
    "ADD": 6, "SUB": 6,
    "MUL": 15, "DIV": 20, "MOD": 20,
    "SHL": 4, "SHR": 4,
    "CMP": 5,
    "OTHER": 3,
}
```

**KEY DIFFERENCE between the two dicts:**
- `OPERATOR_DEPTH_FN` — contains either a number (for fixed-depth ops) OR a callable function (for ops where depth depends on bit width). This is used to compute the `actual_depth` label.
- `OPERATOR_COMPLEXITY` — always a number. This is used as a **feature** for the ML model (Feature #5).

---

## Section 2 — The `VerilogFeatureExtractor` Class (Lines 86–388)

### Step 3: Write the class skeleton

```python
class VerilogFeatureExtractor:
    """
    Parses a single Verilog file and extracts per-signal
    combinational features.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        raw = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        self.code = self._strip_comments(raw)
```

**Why `errors="ignore"` in `read_text`?** Verilog files sometimes contain non-UTF-8 byte sequences in comments. `errors="ignore"` silently drops them instead of raising a `UnicodeDecodeError`.

**Why strip comments immediately in `__init__`?** Comments like `// assign x = ...` could be mistakenly matched by later regex. By stripping them once at init time, all subsequent methods work on clean code.

### Step 4: Write the comment stripper

```python
@staticmethod
def _strip_comments(code: str) -> str:
    code = re.sub(r"//[^\n]*", " ", code)           # Remove // line comments
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.DOTALL)  # Remove /* */ block comments
    return code
```

**Why replace with space instead of empty string?** Removing without replacement can accidentally merge tokens. `"a//comment\nb"` would become `"ab"` — wrong. Replacing with a space gives `"a b"`.

**`re.DOTALL`:** By default, `.` in regex doesn't match newlines. `re.DOTALL` makes `.` match everything including `\n`. This is critical for multi-line `/* ... */` block comments.

---

## Section 3 — Module-Level Parsing (Lines 106–129)

### Step 5: Write module name detection

```python
def get_module_names(self) -> list[str]:
    return re.findall(r"\bmodule\s+(\w+)", self.code)

def get_top_module(self) -> str:
    names = self.get_module_names()
    return names[0] if names else "unknown"
```

**What this matches in Verilog:**
```verilog
module simple_alu_8bit (   ← gets "simple_alu_8bit"
    input [7:0] a, b,
    output [7:0] result
);
```

**`\b`** — word boundary. Ensures we match `module` as a whole word, not as part of `endmodule` or a variable named `module_count`.

### Step 6: Write input port counter

```python
def get_module_inputs(self, module_name: str) -> list[str]:
    pat = rf"\bmodule\s+{re.escape(module_name)}\s*[\(#].*?endmodule"
    m = re.search(pat, self.code, re.DOTALL)
    if not m:
        return []
    body = m.group(0)
    inputs = re.findall(r"\binput\b[^;]*?\b(\w+)\s*(?:,|;|\))", body)
    return inputs

def count_module_inputs(self) -> int:
    inputs = []
    for mod in self.get_module_names():
        inputs.extend(self.get_module_inputs(mod))
    return len(inputs)
```

> **`re.escape(module_name)` is important!** If a module name happened to contain regex special characters (like `.` or `+`), they would be treated as regex operators. `re.escape` prevents this.

---

## Section 4 — Signal Discovery (Lines 133–157)

### Step 7: Write the signal finder

```python
def get_combinational_signals(self) -> list[dict]:
    signals = []
    seen = set()

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
```

**What the regex matches:**

```verilog
output [7:0] result   → kind="output", width_str="7", name="result" → width=8
wire   [3:0] temp     → kind="wire",   width_str="3", name="temp"   → width=4
reg    carry          → kind="reg",    width_str=None, name="carry"  → width=1
```

**Why `width = int(width_str) + 1`?** In Verilog, `[7:0]` means bits 7 down to 0 — that's **8 bits**, not 7. The index of the MSB is 7, so width = 7 + 1 = 8.

**Why skip `clk`, `rst`, etc.?** Clock and reset signals are never combinational logic outputs. Including them would add noise to our dataset.

**Why use `seen` set?** The same signal name might appear multiple times in the code (declaration vs. usage). We only want each signal once.

---

## Section 5 — Feature Extraction (Lines 192–369)

### Step 8: Write the operator detector

```python
def _detect_operator(self, expr: str) -> str:
    """Determine the dominant operator in an expression."""
    if re.search(r"\*", expr) and not re.search(r"\*\*", expr):
        return "MUL"
    if re.search(r"[^=!<>]/[^/]", expr):
        return "DIV"
    if re.search(r"%", expr):
        return "MOD"
    if re.search(r"[+]", expr):
        return "ADD"
    if re.search(r"(?!=)-(?!=)", expr):
        return "SUB"
    if re.search(r"<<|>>", expr):
        return "SHL" if "<<" in expr else "SHR"
    if re.search(r"[<>]", expr):
        return "CMP"
    if re.search(r"\?", expr):
        return "MUX"
    if re.search(r"\^", expr):
        return "XOR"
    if re.search(r"&&|&", expr):
        return "AND"
    if re.search(r"\|\||\|", expr):
        return "OR"
    if re.search(r"~", expr):
        return "NOT"
    return "OTHER"
```

**The order of checks matters!** Multiplication is checked before division, because `//` (division) would be stripped as a comment. Addition is checked before subtraction because a minus sign in `a - b` is less ambiguous. The hierarchy from complex to simple ensures the dominant operator is captured.

### Step 9: Write the fan-in counter

```python
def _count_fanin(self, rhs: str) -> int:
    """Count unique input signals on the RHS."""
    raw = re.findall(r"\b([a-zA-Z_]\w*)\b", rhs)
    exclude = {
        "begin", "end", "if", "else", "case", "casez", "casex",
        "endcase", "for", "integer", "default", "signed", "unsigned",
    }
    return len({x for x in raw if x not in exclude and not x.isdigit()})
```

**Fan-in** = number of unique input signals feeding into a signal's expression.

For `assign result = a + b + carry_in;`, fan-in = 3 (`a`, `b`, `carry_in`).

A higher fan-in means the signal depends on more inputs → likely deeper logic.

### Step 10: Write the fan-out counter

```python
def _count_fanout(self, signal: str) -> int:
    """Count downstream uses of this signal."""
    count = 0
    for m in re.finditer(
        rf"(?:assign\s+\w+\s*=|=)\s*[^;]*\b{re.escape(signal)}\b",
        self.code
    ):
        expr = m.group(0)
        if not re.match(rf"assign\s+{re.escape(signal)}\s*=", expr.strip()):
            count += 1
    return min(count, 20)  # cap at 20 to avoid outliers
```

**Fan-out** = how many other signals' RHS expressions reference this signal.

High fan-out doesn't directly increase depth, but it's a proxy for design complexity.

**Why cap at 20?** Extremely high fan-out (like a clock or global enable) would be an outlier. Capping prevents one signal from distorting the model.

### Step 11: Write the nesting depth counter

```python
def _count_nesting(self) -> int:
    """Maximum if/case nesting depth in the whole file."""
    max_d, cur_d = 0, 0
    for line in self.code.splitlines():
        s = line.strip()
        if re.match(r"\b(if|case[zx]?)\b", s):
            cur_d += 1
            max_d = max(max_d, cur_d)
        if re.match(r"\bend(case)?\b", s):
            cur_d = max(0, cur_d - 1)
    return max_d
```

**Why does nesting matter?** Each `if` or `case` statement in synthesized hardware becomes a **multiplexer (MUX)**. A 3-deep nested `if` means 3 MUX stages in sequence — significantly increasing combinational depth.

---

## Section 6 — The Depth Formula (Lines 306–330)

### Step 12: Write the analytical depth calculator

```python
def compute_depth(self, features: dict) -> int:
    """
    Analytical combinational depth:
      base_depth  = operator gate stages (width-scaled)
      mux_penalty = nesting_depth * 2   (each if/case adds 1 MUX = 2 gate levels)
      fanin_log   = ceil(log2(fanin+1)) (fan-in tree overhead)
    Total = base + mux + fanin_log  (clamped to [1, 60])
    """
    op   = features["op_type"]
    w    = features["signal_width"]
    nest = features["nesting_depth"]
    fin  = features["fanin"]

    fn   = OPERATOR_DEPTH_FN.get(op, 3)
    base = fn(w) if callable(fn) else fn     # Call function if width-dependent

    mux_penalty = nest * 2
    fanin_log   = math.ceil(math.log2(max(fin, 2)))

    if features.get("is_registered"):
        return 0    # Flip-flop output has 0 combinational depth

    depth = base + mux_penalty + fanin_log
    return max(1, min(depth, 60))    # Clamp: at least 1, at most 60
```

**Example calculation for an 8-bit adder with 3-deep nesting:**
```
base      = _add_depth(8) = 2 * ceil(log2(8)) = 2 * 3 = 6
mux_penalty = 3 * 2 = 6
fanin_log = ceil(log2(max(3, 2))) = ceil(log2(3)) = ceil(1.58) = 2
total     = 6 + 6 + 2 = 14 gate levels
```

---

## Section 7 — The Public API (Lines 332–447)

### Step 13: Write `extract_signal_features()`

This is the method that ties everything together for **one signal**:

```python
def extract_signal_features(self, signal_name: str) -> dict:
    rhs = self.get_rhs(signal_name) or ""

    op_type = self._detect_operator(rhs) if rhs else "OTHER"
    fanin   = self._count_fanin(rhs) if rhs else 1

    m = re.search(rf"\[(\d+):\d+\]\s+{re.escape(signal_name)}", self.code)
    width = int(m.group(1)) + 1 if m else 1

    nesting = self._count_nesting()

    return {
        "signal_name":           signal_name,
        "module_name":           self.get_top_module(),
        "fanin":                 fanin,
        "fanout":                self._count_fanout(signal_name),
        "signal_width":          width,
        "op_type":               op_type,
        "op_complexity":         OPERATOR_COMPLEXITY.get(op_type, 3),
        "nesting_depth":         nesting,
        "operation_count":       self._count_operations(rhs),
        "has_mul":               int("*" in rhs),
        "has_add":               int("+" in rhs or ("-" in rhs)),
        "in_loop":               self._is_in_loop(signal_name),
        "is_registered":         self._is_registered(signal_name),
        "module_input_count":    self.count_module_inputs(),
        "conditional_mux_count": self._count_mux_branches(signal_name),
    }
```

### Step 14: Write the `__main__` block for standalone use

```python
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    rtl_dir      = project_root / "data" / "rtl"
    output_csv   = project_root / "data" / "dataset.csv"
    extract_features(str(rtl_dir), str(output_csv))
```

**`Path(__file__).resolve().parents[1]`** — this gets the project root directory:
- `__file__` = `k:\project\features\extractor.py`
- `.resolve()` = absolute path
- `.parents[0]` = `k:\project\features\`
- `.parents[1]` = `k:\project\`  ← This is what we want

---

## Running the Extractor

```bash
# From the project root:
python features/extractor.py
```

**Expected output:**
```
Processing 150 Verilog files from k:\project\data\rtl
  [!] Skipping some_file.v: ...   (occasional warnings are OK)

[DONE] Extracted 243 signal rows -> k:\project\data\dataset.csv
```

---

## The 13 Features — Summary

| # | Feature | Type | How Extracted |
|---|---------|------|---------------|
| 1 | `fanin` | int | Count unique identifiers on RHS |
| 2 | `fanout` | int | Count RHS appearances of signal |
| 3 | `signal_width` | int | Parse `[N-1:0]` declaration |
| 4 | `op_type` | str | Regex priority check on RHS |
| 5 | `op_complexity` | int | Lookup table |
| 6 | `nesting_depth` | int | Count if/case depth |
| 7 | `operation_count` | int | Count operators in expression |
| 8 | `has_mul` | 0/1 | `"*" in rhs` |
| 9 | `has_add` | 0/1 | `"+" in rhs` |
| 10 | `in_loop` | 0/1 | Regex for `for`/`genvar` block |
| 11 | `is_registered` | 0/1 | Check posedge/negedge block |
| 12 | `module_input_count` | int | Count `input` port declarations |
| 13 | `conditional_mux_count` | int | Count `?` and `case` branches |

---

> **[<< Part 3: Requirements](./PART_03_REQUIREMENTS.md)** | **[Next: Dataset Prep >>](./PART_05_DATASET_PREP.md)**
