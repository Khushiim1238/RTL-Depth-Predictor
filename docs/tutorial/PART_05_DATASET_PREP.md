# Part 5 — Preparing the Dataset (`src/prepare_dataset.py`)

> **[<< Part 4: Feature Extractor](./PART_04_FEATURE_EXTRACTOR.md)** | **[Next: Training >>](./PART_06_TRAINING.md)**

---

## What You Will Learn

- Where the Verilog training data comes from
- How to download open-source RTL designs from GitHub
- How to generate synthetic Verilog locally
- How `prepare_dataset.py` orchestrates the whole data pipeline
- What `dataset.csv` looks like and why its structure matters

---

## The Big Picture: Where Does Training Data Come From?

This is an ML project on a **very niche domain** — chip design. There is no `pip install verilog-dataset`. You must gather real Verilog designs from open-source repositories.

The project uses **4 data sources**:

| Source | Repository | Designs | Why chosen |
|--------|-----------|---------|------------|
| RTLLM | `hkust-zhiyao/RTLLM` | ~50 files | Curated for EDA ML research |
| VTR | `verilog-to-routing/vtr-verilog-to-routing` | ~60 files | Academic FPGA benchmarks |
| VerilogEval | `NVlabs/verilog-eval` | ~80 files | Diverse synthesizable modules |
| Local | This repo (generated) | 55 files | Covers all circuit categories |

---

## Step 5.1 — Download RTL Files from GitHub

```bash
python data/scripts/download_rtl.py
```

**What this script does internally:**

```python
import requests
from pathlib import Path

# Example: downloading from RTLLM GitHub repo
api_url = "https://api.github.com/repos/hkust-zhiyao/RTLLM/contents/..."
response = requests.get(api_url)
files = response.json()

for file in files:
    if file["name"].endswith(".v"):
        content = requests.get(file["download_url"]).text
        Path(f"data/rtl/rtllm/{file['name']}").write_text(content)
```

> **IMPORTANT:** GitHub has API rate limits. If you see `403 Forbidden` errors, you have hit the rate limit. Wait 60 seconds and retry. You can also add a GitHub personal access token for higher limits.

**After running, you should see:**
```
data/rtl/
  rtllm/       → ~50 .v files
  vtr/         → ~60 .v files
  verilogeval/ → ~80 .v files
```

---

## Step 5.2 — Generate Local RTL Designs

```bash
python data/scripts/generate_rtl_local.py
```

**Why generate locally?** Downloaded RTL designs may not cover all circuit types we care about. We want to ensure the training data includes:
- Simple AND/OR combinational logic
- 8-bit and 16-bit adders
- Multipliers (very deep logic)
- Barrel shifters
- Comparators
- MUX trees
- Deeply nested if/case designs

**The generator script creates Verilog files programmatically**, like:

```python
# Example: generate a simple 8-bit adder
content = """
module ripple_carry_adder_8bit (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] sum,
    output       cout
);
    assign {cout, sum} = a + b + cin;
endmodule
"""
Path("data/rtl/local/ripple_carry_adder_8bit.v").write_text(content)
```

This ensures we have exactly the types of circuits that exercise each part of our feature extractor.

---

## Step 5.3 — The One-Stop Script: `prepare_dataset.py`

This script (in `src/`) does everything in one command:

```bash
python src/prepare_dataset.py
```

Let's trace through its code section by section.

### Section A: Argument Parsing

```python
parser = argparse.ArgumentParser(description="Prepare RTL dataset")
parser.add_argument("--rtl-dir", default=str(RTL_DIR),
                    help=f"Root RTL directory (default: {RTL_DIR})")
parser.add_argument("--out", default=str(OUT_CSV),
                    help=f"Output CSV path (default: {OUT_CSV})")
parser.add_argument("--no-generate", action="store_true",
                    help="Skip local design generation")
args = parser.parse_args()
```

**Why use `argparse`?** It makes the script flexible. You can override defaults without editing the code:

```bash
# Use a different RTL folder:
python src/prepare_dataset.py --rtl-dir data/my_custom_rtl

# Skip generating local files (if you already have them):
python src/prepare_dataset.py --no-generate
```

### Section B: Ensure Local Designs Exist

```python
def _ensure_local_designs():
    local_dir = RTL_DIR / "local"
    if local_dir.exists() and any(local_dir.glob("*.v")):
        print(f"  Local RTL already present ({len(...)} files)")
        return                          # Already done — skip
    print("  Generating local RTL designs ...")
    # ... dynamically import and run generate_rtl_local.py
```

**This is a guard pattern** — it checks before doing work, avoiding re-generation on repeated runs. This matters because `generate_rtl_local.py` can take 10–30 seconds.

### Section C: Count and Validate Files

```python
v_files = list(rtl_dir.rglob("*.v"))   # rglob = recursive glob
if not v_files:
    print(f"\n[!] No .v files found under {rtl_dir}")
    sys.exit(1)

print(f"\n  Found {len(v_files)} Verilog files under {rtl_dir}")
```

**`rglob("*.v")`** — searches all subdirectories recursively. `glob("*.v")` only searches the immediate directory.

### Section D: Extract Features to CSV

```python
from feature_extraction import extract_features
rows = extract_features(str(rtl_dir), str(out_csv))
```

This calls the `extract_features()` function from `src/feature_extraction.py` (which is identical to `features/extractor.py`). It walks every `.v` file and produces `data/dataset.csv`.

---

## Step 5.4 — Understanding `dataset.csv`

After running the data pipeline, open `data/dataset.csv`. You'll see something like:

```
signal_name,module_name,fanin,fanout,signal_width,op_type,op_complexity,...,actual_depth,source_file
sum,ripple_carry_adder_8bit,3,0,8,ADD,6,0,3,0,1,0,0,3,0,6,ripple_carry_adder_8bit.v
product,array_multiplier_8bit,2,1,8,MUL,15,0,2,1,0,0,0,2,0,14,array_multiplier_8bit.v
out,and_gate,2,0,1,AND,1,0,1,0,0,0,0,2,0,1,and_gate.v
```

### Column Breakdown

| Column | Example | Notes |
|--------|---------|-------|
| `signal_name` | `sum` | Name in Verilog code |
| `module_name` | `ripple_carry_adder_8bit` | Verilog module |
| `fanin` | `3` | Number of inputs |
| `fanout` | `0` | Number of downstream uses |
| `signal_width` | `8` | Bit width |
| `op_type` | `ADD` | Dominant operator |
| `op_complexity` | `6` | Complexity score |
| `nesting_depth` | `0` | if/case nesting |
| `operation_count` | `3` | Operators in expression |
| `has_mul` | `0` | Boolean: has `*` |
| `has_add` | `1` | Boolean: has `+` |
| `in_loop` | `0` | Inside for loop |
| `is_registered` | `0` | Flip-flop output |
| `module_input_count` | `3` | Module input ports |
| `conditional_mux_count` | `0` | MUX branches |
| **`actual_depth`** | **`6`** | **TARGET LABEL** |
| `source_file` | `ripple_carry_adder_8bit.v` | For debugging |

> **The `actual_depth` column is the label** — what we're trying to predict. Everything else is input features.

---

## What to Keep in Mind

### Data Quality Checks

Before training, mentally verify:
1. **Enough rows:** You need at least 50 rows; 200+ is better.
2. **Diverse op_types:** Check that ADD, MUL, AND, MUX, etc. all appear.
3. **Depth range:** Should span from 1 to ~30 or more.
4. **No all-zeros:** A column that's always 0 adds no information.

```bash
# Quick check in Python:
python -c "
import pandas as pd
df = pd.read_csv('data/dataset.csv')
print(df.shape)
print(df['actual_depth'].describe())
print(df['op_type'].value_counts())
"
```

### Common Problems and Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `No .v files found` | Wrong directory path | Check `data/rtl/` has subdirs |
| Only 5–10 rows | All files failed | Check for encoding errors in .v files |
| All depths = 1 | `is_registered` bug | Verify `_is_registered()` logic |
| `KeyError: actual_depth` | CSV column missing | Re-run extractor.py |

---

## Checkpoint

Run the full pipeline and verify:

```bash
# Step 1: Get data
python data/scripts/download_rtl.py          # Optional (needs internet)
python data/scripts/generate_rtl_local.py    # Required

# Step 2: Extract features
python features/extractor.py

# Step 3: Verify CSV
python -c "
import pandas as pd
df = pd.read_csv('data/dataset.csv')
print(f'Rows: {len(df)}, Columns: {df.shape[1]}')
print(df.head(3))
"
```

**Expected:**
```
Rows: 200+, Columns: 17
   signal_name    module_name  fanin  ...  actual_depth  source_file
0          sum  ripple_carry_...   3  ...             6  ripple...v
...
```

---

> **[<< Part 4: Feature Extractor](./PART_04_FEATURE_EXTRACTOR.md)** | **[Next: Training >>](./PART_06_TRAINING.md)**
