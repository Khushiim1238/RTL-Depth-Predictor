# Part 9 — Pro Tips, Common Mistakes & Windows-Specific Issues

> **[<< Part 8: Inference](./PART_08_INFERENCE.md)** | **[<< Overview](./PART_00_OVERVIEW.md)**

---

## What You Will Learn

- The most common mistakes and how to avoid them
- Windows-specific problems (encoding, paths, PowerShell)
- How `fix_unicode.py` works and when to use it
- How to debug the feature extractor
- Performance tips
- Checklist before submitting / presenting the project

---

## 1. The Most Common Mistake: Working Directory

### Problem
```
ModuleNotFoundError: No module named 'features'
```

### Cause
You ran the script from a subdirectory:
```bash
cd k:\project\models
python train.py   # WRONG — can't find features/ from here
```

### Fix
Always run from the **project root**:
```bash
cd k:\project
python models/train.py   # CORRECT — uses forward slash or backslash
```

**How scripts find paths:**
```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
```
This always resolves to `k:\project` regardless of working directory. But `sys.path` still needs to include the root for imports.

---

## 2. Windows Encoding Issues (`fix_unicode.py`)

### The Problem
Python's `print()` on Windows uses the `cp1252` encoding by default. Characters like `✓`, `→`, `±`, `⚠️` cannot be encoded in cp1252, causing:

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2713' in position 5
```

### What `fix_unicode.py` Does
It scans all Python source files and replaces Unicode symbols in `print()` statements with ASCII equivalents:

```python
replacements = {
    "\u2713": "[OK]",   # ✓
    "\u2192": "->",     # →
    "\u00b1": "+-",     # ±
    "\u26a0": "[!]",    # ⚠
    "\u274c": "[ERR]",  # ❌
    # ... etc.
}
```

### When to Run It

```bash
# Run this if you see UnicodeEncodeError on Windows:
python fix_unicode.py
```

**What it changes:**
```python
# Before:
print(f"  ✓ Timing OK → no violation")
# After:
print(f"  [OK] Timing OK -> no violation")
```

### The Better Fix (for new code)
Set the environment variable before running scripts:

```powershell
# PowerShell:
$env:PYTHONIOENCODING = "utf-8"
python predict.py
```

Or add to the top of each script:
```python
import sys
sys.stdout.reconfigure(encoding='utf-8')  # Python 3.7+
```

---

## 3. Virtual Environment Not Activated

### Symptoms
```
ModuleNotFoundError: No module named 'numpy'
ModuleNotFoundError: No module named 'xgboost'
```
(Even though you installed them!)

### Fix
```powershell
# Always activate first:
venv\Scripts\Activate.ps1

# Verify it's active — prompt should show (venv):
(venv) k:\project>
```

### PowerShell Script Execution Policy Error
```
venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled
```

Fix:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 4. GitHub Rate Limiting When Downloading RTL

### Symptom
```
requests.exceptions.HTTPError: 403 Client Error: rate limit exceeded
```

### Fix
GitHub allows 60 unauthenticated API requests per hour. Add a token:

```python
# In data/scripts/download_rtl.py, pass a header:
headers = {"Authorization": "token YOUR_GITHUB_TOKEN"}
response = requests.get(url, headers=headers)
```

Or just wait 60 minutes, or use the locally generated designs only:
```bash
python data/scripts/generate_rtl_local.py   # No internet needed
python features/extractor.py
```

---

## 5. Dataset Too Small (< 50 rows)

### Symptom
Training produces low accuracy, high CV-MAE.

### Causes
- Most `.v` files failed to parse (check for errors during extraction)
- RTL files weren't downloaded

### Debug
```python
python -c "
import pandas as pd
df = pd.read_csv('data/dataset.csv')
print('Total rows:', len(df))
print('Source file counts:')
print(df['source_file'].value_counts().head(10))
print('Depth distribution:')
print(df['actual_depth'].value_counts().sort_index())
"
```

If most rows are depth=1, your extractor might be defaulting `op_type="OTHER"` for everything — check the Verilog files for syntax issues.

---

## 6. The `feature_columns.json` Mismatch

### Symptom
Predictions are wildly wrong even though training metrics were good.

### Cause
`feature_columns.json` is from an old training run with different features than the current `extractor.py`.

### Fix
Always retrain after changing `extractor.py`:
```bash
python features/extractor.py    # Rebuild CSV
python models/train.py          # Retrain (updates feature_columns.json)
```

### How to detect a mismatch:
```python
import json
info = json.load(open("models/feature_columns.json"))
print(info["columns"])
# Compare with what extractor.py produces
from features.extractor import VerilogFeatureExtractor
ext = VerilogFeatureExtractor("data/rtl/local/simple_alu_8bit.v")
feats = ext.extract_signal_features("result")
print(list(feats.keys()))
```

---

## 7. Debugging the Feature Extractor

### Print a single signal's features

```python
from features.extractor import VerilogFeatureExtractor

ext = VerilogFeatureExtractor("data/rtl/local/simple_alu_8bit.v")

# See what signals were found
print(ext.get_combinational_signals())

# Extract features for a specific signal
feats = ext.extract_signal_features("result")
for k, v in feats.items():
    print(f"  {k:25} = {v}")

# See the raw RHS expression
print("RHS:", ext.get_rhs("result"))
```

### Check op_type detection

```python
expr = "a + b + cin"
print(ext._detect_operator(expr))   # Should print "ADD"

expr = "a * b"
print(ext._detect_operator(expr))   # Should print "MUL"
```

---

## 8. Performance Tips

| Optimization | Impact | How |
|-------------|--------|-----|
| `n_jobs=-1` in Random Forest | 3-5x faster training | Already in the code |
| Reduce `n_estimators` to 100 | 3x faster training, small accuracy loss | Edit `train.py` |
| Skip MLP if accuracy is low | MLP rarely wins on this data | Comment out in `build_models()` |
| Pre-compile regex patterns | ~10% faster extraction | Use `re.compile()` at class level |
| Run on SSD vs. HDD | Faster joblib load | Keep project on SSD |

---

## 9. Key Concepts to Remember

| Concept | One-Liner |
|---------|-----------|
| **Verilog** | Hardware description language for chips |
| **RTL** | Register-Transfer Level — the abstraction we work at |
| **Combinational depth** | Number of gate levels from input to output |
| **Fan-in** | Number of unique inputs to a signal |
| **Fan-out** | Number of signals that use this signal as input |
| **One-hot encoding** | Convert category strings to binary columns |
| **Cross-validation** | Train/evaluate on multiple splits for robust metrics |
| **Pipeline (sklearn)** | Chain preprocessing + model into one `.fit()/.predict()` call |
| **`random_state=42`** | Reproducibility seed — always use the same value |
| **`feature_columns.json`** | Contract between training and inference column order |

---

## 10. Full Pipeline Checklist

Use this before presenting or submitting the project:

```
SETUP:
  [ ] Python 3.10+ confirmed
  [ ] venv activated
  [ ] pip install -r requirements.txt done without errors

DATA:
  [ ] At least 55 .v files exist in data/rtl/
  [ ] dataset.csv has 100+ rows
  [ ] No single op_type dominates (check distribution)

TRAINING:
  [ ] models/best_model.pkl exists
  [ ] models/feature_columns.json exists
  [ ] Best model CV-MAE < 2.0

EVALUATION:
  [ ] results/actual_vs_predicted.png generated
  [ ] results/feature_importance.png generated
  [ ] results/error_distribution.png generated
  [ ] +-1 Accuracy > 75%

INFERENCE:
  [ ] python predict.py --file ... --signal ... runs without error
  [ ] Inference time < 500ms
  [ ] Timing violation flagged when depth * 0.1 > clock_period
```

---

## 11. Final Architecture Summary

```
INPUT:   design.v (Verilog source code)
         signal_name (e.g. "result")
         clock_period (e.g. 1.0 ns)
          |
          v
STEP 1:  VerilogFeatureExtractor
         - Strip comments
         - Find signal declaration (width)
         - Extract RHS expression
         - Compute 13 features
          |
          v
STEP 2:  Feature Alignment (_align_features)
         - One-hot encode op_type
         - Add missing columns (0)
         - Reorder to training column order
          |
          v
STEP 3:  XGBoost model (best_model.pkl)
         - model.predict(X)  →  raw float
         - round() and clamp to [0, ∞)
          |
          v
OUTPUT:  predicted_depth (int)
         estimated_delay (float, ns)
         timing_ok (bool)
         inference_ms (float)
```

---

> **[<< Part 8: Inference](./PART_08_INFERENCE.md)** | **[<< Return to Overview](./PART_00_OVERVIEW.md)**

---

*You have completed the full tutorial! You now understand every line of this project from setup to inference.*
