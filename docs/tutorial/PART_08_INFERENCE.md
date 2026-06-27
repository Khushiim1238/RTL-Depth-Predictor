# Part 8 — Making Predictions (`predict.py` + `inference.py`)

> **[<< Part 7: Evaluation](./PART_07_EVALUATION.md)** | **[Next: Tips & Tricks >>](./PART_09_TIPS_AND_TRICKS.md)**

---

## What You Will Learn

- The 3 ways to use the predictor (CLI, interactive, Python API)
- How `predict.py` connects features → model → output
- How `inference.py` wraps `predict.py` for use as a library
- How feature alignment works at inference time
- How to batch-predict multiple signals

---

## The 3 Usage Modes

### Mode 1: CLI Flags (Recommended)

```bash
python predict.py \
    --file data/rtl/local/simple_alu_8bit.v \
    --signal result \
    --module simple_alu_8bit \
    --clock 1.0
```

**Arguments:**
| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--file` | `-f` | Path to Verilog file | required |
| `--signal` | `-s` | Signal name to analyze | required |
| `--module` | `-m` | Top module name | auto-detected |
| `--clock` | `-c` | Clock period in nanoseconds | `1.0` |
| `--model` | | Path to model .pkl | `models/best_model.pkl` |

### Mode 2: Interactive Prompt

```bash
python predict.py
```

You'll be prompted:
```
  RTL Combinational Depth Predictor v1.0
  Interactive Mode

  Verilog file path  : data/rtl/local/simple_alu_8bit.v
  Signal name        : result
  Top module [simple_alu_8bit]  :        (press Enter to accept)
  Clock period (ns) [1.0]:              (press Enter for default)

  Predicting ...
```

### Mode 3: Python API (Import in Notebooks/Scripts)

```python
from inference import predict_depth

result = predict_depth(
    "data/rtl/local/simple_alu_8bit.v",
    "result",
    "simple_alu_8bit",
    clock_period_ns=1.0
)
print(result["predicted_depth"])   # e.g. 9
```

---

## Section A: How `predict.py` Is Structured

### The `main()` Function and Argument Parser

```python
def main():
    parser = argparse.ArgumentParser(
        description="RTL Combinational Depth Predictor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file",   "-f", help="Path to Verilog (.v) file")
    parser.add_argument("--signal", "-s", help="Signal name to analyze")
    parser.add_argument("--module", "-m", help="Top module name")
    parser.add_argument("--clock",  "-c", type=float, default=1.0)
    parser.add_argument("--model",        default=str(MODEL_PATH))

    args = parser.parse_args()

    # If no --file or --signal given, launch interactive mode
    if not args.file or not args.signal:
        _interactive_mode()
        return

    result = predict_depth(
        verilog_file    = args.file,
        signal_name     = args.signal,
        top_module      = args.module,
        clock_period_ns = args.clock,
        model_path      = args.model,
    )
    _print_result(result)
```

**Design pattern:** The script checks if required arguments are missing and falls back to interactive mode. This "progressive disclosure" UX makes the tool accessible to users who don't remember the flags.

---

## Section B: The `predict_depth()` Function — Step by Step

This is the core function that everything else calls.

### Step 8.1: Validate the input file

```python
def predict_depth(
    verilog_file:    str,
    signal_name:     str,
    top_module:      str | None = None,
    clock_period_ns: float = 1.0,
    model_path:      str | Path = MODEL_PATH,
) -> dict:

    vf = Path(verilog_file)
    if not vf.exists():
        raise FileNotFoundError(f"Verilog file not found: {verilog_file}")
```

**Fail early, fail clearly.** Checking at the top of the function gives a meaningful error message rather than a confusing traceback from deep inside the code.

### Step 8.2: Extract features from the Verilog file

```python
sys.path.insert(0, str(PROJECT_ROOT))
from features.extractor import VerilogFeatureExtractor

ext = VerilogFeatureExtractor(str(vf))

if top_module is None:
    top_module = ext.get_top_module()   # Auto-detect module name

t0    = time.perf_counter()
feats = ext.extract_signal_features(signal_name)
```

**Why `sys.path.insert`?** When running `predict.py` from the project root, Python might not find `features/extractor.py` automatically. Adding `PROJECT_ROOT` to `sys.path` ensures the import works from any working directory.

**Why measure time here?** We start the timer (`t0`) before extraction AND model loading to measure total inference time, which includes disk I/O.

### Step 8.3: Load the model

```python
def _load_model(model_path):
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

model, columns = _load_model(model_path)
```

### Step 8.4: Align features to training column layout

```python
def _align_features(feature_dict: dict, columns: list[str]) -> pd.DataFrame:
    exclude = {"signal_name", "module_name", "source_file"}
    row = {k: v for k, v in feature_dict.items() if k not in exclude}

    df = pd.DataFrame([row])

    # One-hot encode op_type (same as training)
    if "op_type" in df.columns:
        df = pd.get_dummies(df, columns=["op_type"], dtype=int)

    # Add any missing columns (set to 0)
    if columns:
        for col in columns:
            if col not in df.columns:
                df[col] = 0
        df = df[columns]    # Reorder to exact training column order

    return df
```

**This is the most important step for correct inference.**

**The problem:** During training, `op_type` was one-hot encoded into 15+ columns (`op_type_ADD`, `op_type_MUL`, etc.). At inference, a new signal's `op_type` might be `"AND"`, which creates only `op_type_AND = 1` and misses all other columns.

**The solution:**
1. One-hot encode the single inference row
2. Add any columns that exist in training but not in this row (set to 0)
3. Reorder columns to exactly match training order

**Example:**
```
Training columns:  [fanin, fanout, ..., op_type_ADD, op_type_MUL, op_type_AND, ...]
New signal (AND):  [fanin, fanout, ..., op_type_AND=1]
After alignment:   [fanin, fanout, ..., op_type_ADD=0, op_type_MUL=0, op_type_AND=1, ...]
```

### Step 8.5: Make the prediction

```python
X    = _align_features(feats, columns)
pred = float(model.predict(X)[0])    # model.predict() returns array
depth = max(0, round(pred))           # Round to int, clamp to non-negative
inf_ms = (time.perf_counter() - t0) * 1000
```

### Step 8.6: Compute timing estimate

```python
GATE_DELAY_NS = 0.1    # 0.1 ns per gate level (typical 28nm CMOS)

estimated_delay = depth * GATE_DELAY_NS
timing_ok       = estimated_delay <= clock_period_ns
```

**Where does 0.1 ns/gate come from?** In a 28nm CMOS process, a simple gate (NAND2) has a propagation delay of ~50–100 picoseconds. We use 0.1 ns as a conservative average across gate types.

A 1 GHz clock has period = 1.0 ns. If depth = 9, delay = 0.9 ns < 1.0 ns → timing OK.
If depth = 11, delay = 1.1 ns > 1.0 ns → **timing violation!**

### Step 8.7: Return the result dict

```python
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
```

---

## Section C: The Output Format

Running CLI mode prints:

```
+--------------------------------------------------+
|     RTL Combinational Depth Predictor Result     |
+--------------------------------------------------+
  Signal         : result
  Module         : simple_alu_8bit
  Predicted Depth: 9 gate levels
  Est. Delay     : 0.9 ns
  Clock Period   : 1.0 ns
  Timing Status  : [OK] OK - no violation
  Inference Time : 4.23 ms

  Key Features Extracted:
    Fan-in         : 3
    Fan-out        : 2
    Signal width   : 8 bits
    Operator type  : ADD
    Nesting depth  : 0
    Has multiply   : No
```

---

## Section D: `inference.py` — The Library Wrapper

`inference.py` is designed for **programmatic use** (Jupyter notebooks, other scripts, CI tests):

### Batch prediction

```python
from inference import batch_predict

signals = [
    ("data/rtl/local/simple_alu_8bit.v",        "result",  "simple_alu_8bit"),
    ("data/rtl/local/array_multiplier_8bit.v",   "product", "array_multiplier_8bit"),
    ("data/rtl/local/ripple_carry_adder_8bit.v", "sum",     "ripple_carry_adder_8bit"),
]

results = batch_predict(signals, clock_period_ns=1.0)

for r in results:
    status = "OK" if r["timing_ok"] else "VIOLATION"
    print(f"{r['signal']:15} | depth={r['predicted_depth']:3} | {status}")
```

**Output:**
```
result          | depth=  9 | OK
product         | depth= 14 | VIOLATION
sum             | depth=  6 | OK
```

### Getting model information

```python
from inference import get_model_info

info = get_model_info()
print(info["best_model"])    # "XGBoost"
print(len(info["columns"]))  # 24  (number of features)
```

---

## Section E: How `inference.py` Re-exports from `predict.py`

```python
# inference.py
from predict import predict_depth   # re-export
```

This is the "re-export" pattern. Users can write:
```python
from inference import predict_depth   # Works
from predict   import predict_depth   # Also works (same function)
```

`inference.py` is the cleaner, more stable public API. `predict.py` can be thought of as an implementation file that also happens to work as a script.

---

> **[<< Part 7: Evaluation](./PART_07_EVALUATION.md)** | **[Next: Tips & Tricks >>](./PART_09_TIPS_AND_TRICKS.md)**
