# Part 6 — Training ML Models (`models/train.py`)

> **[<< Part 5: Dataset Prep](./PART_05_DATASET_PREP.md)** | **[Next: Evaluation >>](./PART_07_EVALUATION.md)**

---

## What You Will Learn

- How to load and preprocess the dataset for ML
- What one-hot encoding is and why it's needed
- How to train 5 different ML models
- What cross-validation is and why it beats simple train/test split
- How to select the best model automatically
- How to save a trained model to disk

---

## Run Command

```bash
python models/train.py
```

**Expected output (abbreviated):**
```
============================================================
  RTL Depth Predictor - Model Training
============================================================
Loaded dataset: 243 rows, 17 columns
Depth distribution:
  count    243.0
  mean       7.3
  max       30.0

Train: 194 rows | Test: 49 rows

  Training: Linear Regression ...
    MAE=2.10  RMSE=3.45  +-1 acc=52.3%  CV-MAE=2.15
  Training: Decision Tree ...
    MAE=1.20  RMSE=2.10  +-1 acc=73.5%  CV-MAE=1.45
  Training: Random Forest ...
    MAE=0.90  RMSE=1.85  +-1 acc=80.2%  CV-MAE=1.10
  Training: XGBoost ...
    MAE=0.75  RMSE=1.60  +-1 acc=85.1%  CV-MAE=0.95
  Training: MLP Neural Network ...
    MAE=1.50  RMSE=2.80  +-1 acc=65.0%  CV-MAE=1.60

[BEST] Best model: XGBoost  (CV-MAE = 0.95)
   Saved: models/best_model.pkl
   Saved: models/feature_columns.json
```

---

## Section A: Imports and Configuration

At the top of `models/train.py`:

```python
from __future__ import annotations

import os, sys, json, time, math, warnings
import numpy  as np
import pandas as pd
import joblib

from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing   import StandardScaler
from sklearn.linear_model    import LinearRegression
from sklearn.tree            import DecisionTreeRegressor
from sklearn.ensemble        import RandomForestRegressor
from sklearn.neural_network  import MLPRegressor
from sklearn.metrics         import mean_absolute_error, mean_squared_error
from sklearn.pipeline        import Pipeline

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[!] xgboost not installed - using GradientBoostingRegressor.")

warnings.filterwarnings("ignore")
```

**Why wrap XGBoost in try/except?** XGBoost is an optional enhancement. If someone can't install it (e.g., restricted environment), the code still works with sklearn's `GradientBoostingRegressor` as a fallback.

**Why `warnings.filterwarnings("ignore")`?** Scikit-learn and numpy produce many deprecation warnings during cross-validation on small datasets. These clutter the output without providing useful information for this use case.

---

## Section B: Load and Prepare Data

### Step 6.1: Load the CSV

```python
def load_and_prepare(csv_path: Path):
    df = pd.read_csv(csv_path)

    if len(df) < 10:
        sys.exit(
            f"Dataset has only {len(df)} rows — too few to train.\n"
            "Please run the data pipeline first."
        )
```

**Why check for minimum rows?** With fewer than 10 rows:
- `train_test_split` would give 8 training examples — useless
- Cross-validation folds would have 1–2 examples each — meaningless
- The model would severely overfit

### Step 6.2: One-Hot Encode `op_type`

```python
NUMERIC_FEATURES = [
    "fanin", "fanout", "signal_width", "op_complexity",
    "nesting_depth", "operation_count",
    "has_mul", "has_add", "in_loop", "is_registered",
    "module_input_count", "conditional_mux_count",
]
CATEGORICAL_FEATURES = ["op_type"]

df_enc = pd.get_dummies(
    df[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
    columns=CATEGORICAL_FEATURES,
    dtype=int
)
```

**What is one-hot encoding?**

The `op_type` column contains strings like `"ADD"`, `"MUL"`, `"AND"`. ML models work with numbers. One-hot encoding converts one column into many binary columns:

```
Before:              After:
op_type              op_type_ADD  op_type_MUL  op_type_AND  op_type_XOR ...
ADD          →       1            0            0            0
MUL          →       0            1            0            0
AND          →       0            0            1            0
```

**Why not just use numbers like 1=ADD, 2=MUL, 3=AND?** That would imply a numerical ordering (AND > ADD? ADD is half of MUL?) which doesn't exist. One-hot encoding treats each category as completely independent.

### Step 6.3: Save Feature Column Order

```python
feature_cols = list(df_enc.columns)
X = df_enc
y = df["actual_depth"]
return X, y, feature_cols
```

`feature_cols` is the **exact list of column names** after one-hot encoding. This list is saved to `feature_columns.json` and used at inference time to ensure features are in the same order the model was trained on.

> **CRITICAL:** If you train with columns `[fanin, fanout, ..., op_type_ADD, op_type_MUL]` but at inference your DataFrame has columns in a different order or is missing some, the model will produce wrong predictions silently. `feature_columns.json` prevents this.

---

## Section C: Train/Test Split

```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")
```

**80/20 split:** 80% of rows go to training, 20% to testing.

**`random_state=42`:** Sets the random seed. This makes the split **reproducible** — every time you run the script, the same rows go to train and test. Without this, results would change each run.

---

## Section D: Building the 5 Models

### Step 6.4: Model definitions

```python
def build_models() -> dict:
    return {
        # Model 1: Linear Regression (Baseline)
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  LinearRegression()),
        ]),

        # Model 2: Decision Tree
        "Decision Tree": DecisionTreeRegressor(max_depth=12, random_state=42),

        # Model 3: Random Forest
        "Random Forest": RandomForestRegressor(
            n_estimators=200,      # 200 trees in the forest
            max_depth=15,          # Each tree up to 15 levels
            min_samples_leaf=2,    # Leaf must have 2+ samples (prevents overfitting)
            random_state=42,
            n_jobs=-1              # Use all CPU cores
        ),

        # Model 4: XGBoost
        "XGBoost": xgb.XGBRegressor(
            n_estimators=300,      # 300 boosting rounds
            max_depth=6,
            learning_rate=0.05,    # Small steps
            subsample=0.8,         # Use 80% of data per round
            colsample_bytree=0.8,  # Use 80% of features per round
            random_state=42,
            verbosity=0
        ),

        # Model 5: MLP Neural Network
        "MLP Neural Network": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),  # 3 hidden layers
                activation="relu",
                solver="adam",
                max_iter=1000,
                random_state=42,
                early_stopping=True,         # Stop if val loss stops improving
                validation_fraction=0.1,     # 10% of train → val during training
            )),
        ]),
    }
```

**Why use `Pipeline` for Linear Regression and MLP but not for trees?**

`Pipeline` chains preprocessing + model into one object. `StandardScaler` normalizes features (subtracts mean, divides by std deviation). Linear models and neural networks are **sensitive to feature scale** — a feature ranging 0–1000 dominates features ranging 0–1. Tree-based models (Decision Tree, Random Forest, XGBoost) split on thresholds and are **scale-invariant**, so they don't need scaling.

---

## Section E: Training Loop and Metrics

### Step 6.5: Train and evaluate each model

```python
for name, model in models.items():
    print(f"  Training: {name} ...")
    t0 = time.perf_counter()
    model.fit(X_train, y_train)          # TRAIN
    train_s = time.perf_counter() - t0

    metrics = evaluate(model, X_test, y_test)   # EVALUATE on held-out test set
    metrics["Train_time_s"] = round(train_s, 2)

    # 5-FOLD CROSS-VALIDATION
    cv = cross_val_score(model, X, y, cv=5,
                         scoring="neg_mean_absolute_error", n_jobs=-1)
    metrics["CV_MAE_5fold"] = round(-cv.mean(), 3)
```

### Step 6.6: The evaluation function

```python
def evaluate(model, X_test, y_test) -> dict:
    t0    = time.perf_counter()
    y_pred = np.round(model.predict(X_test)).astype(int)   # Round to nearest int
    inf_ms = (time.perf_counter() - t0) * 1000

    mae   = mean_absolute_error(y_test, y_pred)
    rmse  = math.sqrt(mean_squared_error(y_test, y_pred))
    acc1  = float(np.mean(np.abs(y_test.values - y_pred) <= 1) * 100)
    acc2  = float(np.mean(np.abs(y_test.values - y_pred) <= 2) * 100)

    return {
        "MAE":               round(mae, 3),
        "RMSE":              round(rmse, 3),
        "Accuracy_within_1": round(acc1, 1),
        "Accuracy_within_2": round(acc2, 1),
        "Inference_ms":      round(inf_ms, 2),
    }
```

**Metric explanations:**

| Metric | Formula | What "Good" Looks Like |
|--------|---------|------------------------|
| **MAE** | avg(|predicted - actual|) | < 2.0 gate levels |
| **RMSE** | sqrt(avg((predicted - actual)²)) | < 3.0 (penalizes large errors more) |
| **±1 Accuracy** | % predictions within 1 of actual | > 75% |
| **±2 Accuracy** | % predictions within 2 of actual | > 90% |

**Why round predictions to integers?** Combinational depth is always a whole number (you can't have 6.3 gate levels). The model predicts a float; we round it.

---

## Section F: What Is Cross-Validation?

### The Problem with a Single Train/Test Split

If you get lucky with the split (test set happens to be easy), your metrics look great. If unlucky, they look terrible. One split is not representative.

### 5-Fold Cross-Validation

```
Full Dataset (200 rows)
│
├── Fold 1: [1-40 = TEST]  [41-200 = TRAIN]  → MAE_1
├── Fold 2: [41-80 = TEST] [1-40, 81-200 = TRAIN] → MAE_2
├── Fold 3: [81-120 = TEST] ...               → MAE_3
├── Fold 4: [121-160 = TEST] ...              → MAE_4
└── Fold 5: [161-200 = TEST] ...              → MAE_5

CV_MAE = average(MAE_1, MAE_2, MAE_3, MAE_4, MAE_5)
```

The model is trained 5 times on 5 different 80/20 splits. The average MAE is a **robust estimate** of real-world performance.

**Why use CV to select the best model?** We use `CV_MAE_5fold` (not the single-split MAE) to pick the best model because it's a more reliable estimate.

```python
best_name = min(results, key=lambda n: results[n]["CV_MAE_5fold"])
```

---

## Section G: Saving Artifacts

### Step 6.7: Save the trained model

```python
model_path = MODELS_DIR / "best_model.pkl"
joblib.dump(best_model, model_path)
print(f"   Saved: {model_path}")
```

**`.pkl` = pickle format.** `joblib` serializes the entire model object (all tree structures, weights, etc.) into a binary file.

**File size:** ~500KB for a 300-tree XGBoost model. ~5MB for a 200-tree Random Forest.

### Step 6.8: Save feature columns

```python
feat_path = MODELS_DIR / "feature_columns.json"
with open(feat_path, "w") as fh:
    json.dump({"columns": feature_cols, "best_model": best_name}, fh, indent=2)
```

**`feature_columns.json` example:**
```json
{
  "columns": [
    "fanin", "fanout", "signal_width", "op_complexity",
    "nesting_depth", "operation_count", "has_mul", "has_add",
    "in_loop", "is_registered", "module_input_count",
    "conditional_mux_count", "op_type_ADD", "op_type_AND",
    "op_type_CMP", "op_type_DIV", "op_type_MUL", "op_type_MUX",
    "op_type_NOT", "op_type_OR", "op_type_OTHER", "op_type_SHL",
    "op_type_SHR", "op_type_XOR"
  ],
  "best_model": "XGBoost"
}
```

---

## What to Keep in Mind

| Warning | Detail |
|---------|--------|
| **Random state matters** | Always use `random_state=42` for reproducibility |
| **More data = better model** | If MAE is high, try adding more Verilog files |
| **XGBoost is slow on first run** | It compiles C++ code on first use — be patient |
| **MLP may converge slowly** | `max_iter=1000` with `early_stopping=True` prevents infinite loops |
| **CV is slow** | 5 folds × 5 models = 25 training runs — can take 2–5 minutes |

---

> **[<< Part 5: Dataset Prep](./PART_05_DATASET_PREP.md)** | **[Next: Evaluation >>](./PART_07_EVALUATION.md)**
