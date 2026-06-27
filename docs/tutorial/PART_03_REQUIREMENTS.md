# Part 3 — Dependencies Deep-Dive (requirements.txt)

> **[<< Part 2: Structure](./PART_02_PROJECT_STRUCTURE.md)** | **[Next: Feature Extractor >>](./PART_04_FEATURE_EXTRACTOR.md)**

---

## What You Will Learn

- What every line in `requirements.txt` does
- Why each library was chosen (not just "what it does")
- How they interact with each other in this project
- What would break if you removed each one

---

## The File: `requirements.txt`

Open `k:\project\requirements.txt`. Here is what it contains:

```
numpy>=1.24
pandas>=2.0
scikit-learn>=1.3
xgboost>=2.0
matplotlib>=3.7
seaborn>=0.12
joblib>=1.3
requests>=2.31
pathlib2; python_version<"3.4"
```

Let's go through each one in detail.

---

## Library 1: `numpy` — The Number Engine

**What it is:** NumPy (Numerical Python) provides fast array operations.

**Where we use it in this project:**

In `models/train.py` and `eval/evaluate.py`:
```python
import numpy as np

# Rounding predictions to nearest integer depth
y_pred = np.round(model.predict(X_test)).astype(int)

# Computing +-1 accuracy
acc1 = float(np.mean(np.abs(y_test.values - y_pred) <= 1) * 100)
```

**Why it matters:** Scikit-learn and XGBoost both return NumPy arrays. Without NumPy, no ML computation works.

**What breaks without it:** Everything in `train.py`, `evaluate.py`, and `predict.py`.

---

## Library 2: `pandas` — The Data Table Handler

**What it is:** Pandas provides DataFrames — spreadsheet-like tables in Python.

**Where we use it in this project:**

In `models/train.py` (loading the dataset):
```python
import pandas as pd

df = pd.read_csv("data/dataset.csv")           # Load CSV as DataFrame
df = df.dropna(subset=["actual_depth"])         # Drop rows with missing depth
df_enc = pd.get_dummies(df[...], columns=["op_type"], dtype=int)  # One-hot encode
```

In `predict.py` (aligning features for inference):
```python
df = pd.DataFrame([row])                        # Single feature dict → table
df = pd.get_dummies(df, columns=["op_type"])    # Match training encoding
df = df[columns]                                # Align column order exactly
```

**Why it matters:** The dataset has mixed types — numbers AND categorical strings (`op_type`). Pandas handles both seamlessly.

**What breaks without it:** `train.py`, `evaluate.py`, and `predict.py` all fail.

---

## Library 3: `scikit-learn` — The ML Toolkit

**What it is:** The most widely-used Python ML library. Provides model classes, preprocessing, evaluation, and pipelines.

**Where we use it in this project:**

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing   import StandardScaler
from sklearn.linear_model    import LinearRegression
from sklearn.tree            import DecisionTreeRegressor
from sklearn.ensemble        import RandomForestRegressor
from sklearn.neural_network  import MLPRegressor
from sklearn.metrics         import mean_absolute_error, mean_squared_error
from sklearn.pipeline        import Pipeline
```

- `train_test_split` — splits data into 80% train / 20% test
- `cross_val_score` — 5-fold cross-validation to find best model fairly
- `StandardScaler` — normalizes features for Linear Regression and MLP
- `Pipeline` — chains scaler + model into one object so you can call `.fit()` and `.predict()` on both together
- `LinearRegression` — baseline model
- `DecisionTreeRegressor` — simple tree model
- `RandomForestRegressor` — ensemble of many trees
- `MLPRegressor` — Multi-layer Perceptron (neural network)
- `mean_absolute_error`, `mean_squared_error` — evaluation metrics

**Why it matters:** Provides a unified `.fit(X, y)` / `.predict(X)` interface for every model. You can swap models without changing any other code.

---

## Library 4: `xgboost` — The Champion Model

**What it is:** eXtreme Gradient Boosting — a highly optimized gradient boosted tree library. Usually wins on tabular data.

**Where we use it in this project:**

```python
import xgboost as xgb

model = xgb.XGBRegressor(
    n_estimators=300,      # 300 trees
    max_depth=6,           # Each tree max 6 levels deep
    learning_rate=0.05,    # Small steps = more stable
    subsample=0.8,         # Use 80% of data per tree (prevents overfitting)
    colsample_bytree=0.8,  # Use 80% of features per tree
    random_state=42,
    verbosity=0            # Silent mode
)
```

**Why not just use RandomForest?**
XGBoost builds trees **sequentially**, where each new tree corrects the errors of the previous ones. This makes it more accurate on structured/tabular data. Random Forest builds trees **independently** in parallel, which is faster but slightly less accurate.

**Fallback:** If XGBoost is not installed, the code automatically falls back to scikit-learn's `GradientBoostingRegressor`.

---

## Library 5: `matplotlib` — The Charting Engine

**What it is:** The standard Python plotting library.

**Where we use it in this project:**

In `eval/evaluate.py`:
```python
import matplotlib
matplotlib.use("Agg")   # IMPORTANT: non-interactive backend (no window popup)
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(y_true, y_pred, ...)           # Scatter plot
ax.plot([lo, hi], [lo, hi], ...)          # Perfect-fit diagonal line
fig.savefig("results/actual_vs_predicted.png", dpi=150)
```

> **IMPORTANT:** `matplotlib.use("Agg")` must be called **before** importing `pyplot`. It switches to a non-display backend, which means it saves to files instead of opening a window. This is required when running on servers or in scripts (not Jupyter notebooks).

**What breaks without it:** The 3 result plots cannot be generated.

---

## Library 6: `seaborn` — The Style Layer

**What it is:** A statistical visualization library built on top of matplotlib. Provides prettier defaults.

**In this project:** Imported but primarily used for color palettes and plot styling. The main plotting uses matplotlib directly.

**Why include it?** When you run notebooks (`notebooks/`) for exploration, seaborn's clean style makes plots more readable.

---

## Library 7: `joblib` — The Model Saver

**What it is:** A library for serializing (saving/loading) Python objects efficiently, especially NumPy arrays and ML models.

**Where we use it in this project:**

Saving the model (in `train.py`):
```python
import joblib
joblib.dump(best_model, "models/best_model.pkl")
```

Loading the model (in `predict.py`):
```python
model = joblib.load("models/best_model.pkl")
```

**Why not use Python's built-in `pickle`?**
`joblib` is optimized for large NumPy arrays (which is what model weights are). It can save/load them **10-100x faster** than pickle, and it supports memory-mapped loading (which reduces RAM usage for large models).

---

## Library 8: `requests` — The Downloader

**What it is:** HTTP library for making web requests.

**Where we use it in this project:**

In `data/scripts/download_rtl.py`:
```python
import requests

response = requests.get("https://api.github.com/repos/hkust-zhiyao/RTLLM/...")
```

It downloads open-source Verilog files from GitHub repositories to populate our training data.

**What breaks without it:** You cannot automatically download RTL files from GitHub. You'd need to manually download them.

---

## Library 9: `pathlib2` — Backward Compatibility

```
pathlib2; python_version<"3.4"
```

**What it is:** A backport of Python 3.4+'s `pathlib` module.

**Why it's there:** The `;` syntax means "only install if Python version < 3.4". Since you're using Python 3.10+, **this is never installed**. It's there as a safety net for very old environments.

**In the code, we use:**
```python
from pathlib import Path    # Standard library in Python 3.4+

PROJECT_ROOT = Path(__file__).resolve().parent
rtl_dir = PROJECT_ROOT / "data" / "rtl"   # / operator joins paths!
```

The `Path` class is much cleaner than string concatenation for file paths.

---

## Summary Table

| Library | Role | Without It |
|---------|------|------------|
| `numpy` | Array math, rounding, accuracy | All ML fails |
| `pandas` | CSV loading, DataFrame ops, one-hot encoding | Data loading fails |
| `scikit-learn` | 4 of 5 ML models, metrics, train/test split | Training fails |
| `xgboost` | Best model (gradient boosting) | Falls back to sklearn GB |
| `matplotlib` | Save result charts to PNG | No charts saved |
| `seaborn` | Pretty plot styling | Plots still work, less styled |
| `joblib` | Save/load `.pkl` model files | Can't persist trained model |
| `requests` | Download RTL files from GitHub | Can't auto-download data |

---

> **[<< Part 2: Structure](./PART_02_PROJECT_STRUCTURE.md)** | **[Next: Feature Extractor >>](./PART_04_FEATURE_EXTRACTOR.md)**
