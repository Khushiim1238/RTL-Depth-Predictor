# Part 2 — Understanding the Project Structure

> **[<< Part 1: Setup](./PART_01_SETUP.md)** | **[Next: Requirements >>](./PART_03_REQUIREMENTS.md)**

---

## What You Will Learn

- What every folder and file does
- How data flows through the system
- Which files you write first, and which depend on others
- The "chain of responsibility" — how each script hands off to the next

---

## The Full Project Tree (Annotated)

```
k:\project\
│
│   predict.py              ← ENTRY POINT: CLI/interactive prediction
│   inference.py            ← API wrapper: import in notebooks/scripts
│   fix_unicode.py          ← Utility: fixes Windows encoding issues
│   requirements.txt        ← All Python dependencies listed here
│   README.md               ← Project overview (for GitHub)
│
├── features/               ← STEP 1 of pipeline: reads .v files
│   ├── extractor.py        ← THE HEART: extracts 13 features per signal
│   └── synthesis_parser.py ← Parses synthesis reports (depth labels)
│
├── src/                    ← Source scripts (some mirror features/)
│   ├── prepare_dataset.py  ← One-stop script: generate + extract + save CSV
│   ├── feature_extraction.py ← Same as features/extractor.py (used by src/)
│   ├── train_models.py     ← Trains all 5 models, saves best
│   ├── save_model.py       ← Serializes models to .pkl files
│   ├── parse_depth.py      ← Depth parsing utilities
│   └── auto_synth.py       ← (Advanced) Auto-synthesis interface
│
├── models/                 ← STEP 2 output: trained model artifacts
│   ├── train.py            ← Entry point to train (mirrors src/train_models.py)
│   ├── best_model.pkl      ← Saved best model (binary file, ~500KB)
│   ├── feature_columns.json ← Feature names used during training
│   └── model_info.txt      ← Human-readable model summary
│
├── data/                   ← Raw data lives here
│   ├── dataset.csv         ← 200+ rows of signals with 13 features + depth label
│   ├── rtl/                ← Verilog (.v) files from open-source repos
│   │   ├── rtllm/          ← From hkust-zhiyao/RTLLM (GitHub)
│   │   ├── vtr/            ← From verilog-to-routing (GitHub)
│   │   ├── verilogeval/    ← From NVlabs (GitHub)
│   │   └── local/          ← Locally generated designs (55 files)
│   ├── scripts/
│   │   ├── download_rtl.py     ← Downloads .v files from GitHub
│   │   └── generate_rtl_local.py ← Generates local .v files
│   └── synthesis_reports/  ← (Optional) Yosys synthesis output
│
├── eval/
│   └── evaluate.py         ← STEP 3: loads model, runs metrics, plots charts
│
└── results/                ← All output charts and comparison JSON
    ├── model_comparison.json
    ├── actual_vs_predicted.png
    ├── feature_importance.png
    └── error_distribution.png
```

---

## The Data Flow — How Everything Connects

Think of this project as an **assembly line**:

```
[Verilog .v Files]
       |
       | (features/extractor.py reads them)
       v
[data/dataset.csv]
       |
       | (models/train.py reads it)
       v
[models/best_model.pkl + feature_columns.json]
       |
       | (predict.py + inference.py load it)
       v
[Prediction: "signal X has depth 9"]
```

Each step produces an **artifact** that the next step consumes. If any step is missing, the next step will fail with a clear error.

---

## File Relationships — What Imports What

```
predict.py
  └── imports → features/extractor.py  (VerilogFeatureExtractor)
  └── loads   → models/best_model.pkl  (joblib)
  └── loads   → models/feature_columns.json

inference.py
  └── re-exports → predict.py (predict_depth)
  └── adds batch_predict(), get_model_info()

models/train.py
  └── reads   → data/dataset.csv
  └── imports → sklearn, xgboost, numpy, pandas
  └── writes  → models/best_model.pkl
  └── writes  → models/feature_columns.json

eval/evaluate.py
  └── reads   → data/dataset.csv
  └── loads   → models/best_model.pkl
  └── writes  → results/*.png

features/extractor.py
  └── reads   → any .v (Verilog) file
  └── uses    → re, math, csv, pathlib (standard library only)
```

> **Key Insight:** `features/extractor.py` has **zero third-party dependencies**.
> It only uses Python's standard library. This makes it very portable.

---

## The "Creation Order" — What to Write First

When building this from scratch, create files in this order:

```
ORDER    FILE                        REASON
  1.     requirements.txt            Defines what libraries you need
  2.     features/extractor.py       Core logic — everything depends on this
  3.     data/scripts/*.py           Get data to process
  4.     data/dataset.csv            Created by extractor.py (auto-generated)
  5.     models/train.py             Needs dataset.csv to exist
  6.     models/best_model.pkl       Created by train.py (auto-generated)
  7.     eval/evaluate.py            Needs model + dataset
  8.     predict.py                  Brings everything together
  9.     inference.py                API wrapper around predict.py
```

---

## Key Files to Pay Close Attention To

### 1. `features/extractor.py` — The Heart of the Project
This single file does the **most important work**. It:
- Reads raw Verilog text
- Strips comments
- Finds signals using regex
- Extracts 13 features per signal
- Computes analytical depth labels using EDA formulas

### 2. `models/best_model.pkl` — The Trained Brain
This binary file is what makes predictions possible. Without it, `predict.py` will fail. It is created by running `models/train.py`.

### 3. `models/feature_columns.json` — The Alignment Contract
During training, features are one-hot encoded (operator type becomes multiple binary columns). This JSON file remembers the **exact column order** used during training, so inference produces the same feature shape.

---

## What to Keep in Mind

- **Never run scripts from inside subdirectories.** Always `cd k:\project` first.
- **`data/dataset.csv` is auto-generated** — do not edit it manually.
- **`models/best_model.pkl` is auto-generated** — do not commit large `.pkl` files to Git without LFS.
- **`features/extractor.py` and `src/feature_extraction.py` have the same code** — the `src/` version is used internally by `prepare_dataset.py` via `importlib`.

---

> **[<< Part 1: Setup](./PART_01_SETUP.md)** | **[Next: Requirements >>](./PART_03_REQUIREMENTS.md)**
