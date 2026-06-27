# Part 7 — Evaluating the Model (`eval/evaluate.py`)

> **[<< Part 6: Training](./PART_06_TRAINING.md)** | **[Next: Inference >>](./PART_08_INFERENCE.md)**

---

## What You Will Learn

- How to load a saved model and reproduce the test split
- How each evaluation metric is computed
- How the 3 visualization charts are generated
- Why dark-theme charts look more professional
- How to interpret evaluation results

---

## Run Command

```bash
python eval/evaluate.py
```

**Expected output:**
```
============================================================
  RTL Depth Predictor - Model Evaluation
============================================================

Evaluating on 49 test samples ...

  Model: XGBoost
  ----------------------------------------
  MAE                       0.872
  RMSE                      1.643
  Accuracy_within_1         83.7
  Accuracy_within_2         93.9
  Max_error                 8
  Median_error              0.5
  ----------------------------------------

  [OK] +-1 Accuracy: 83.7% - TARGET MET (>=75%)

  Saved: results/evaluation_metrics.json

  Generating plots ...
  [CHART] Saved: results/actual_vs_predicted.png
  [CHART] Saved: results/feature_importance.png
  [CHART] Saved: results/error_distribution.png

[OK] Evaluation complete! Plots saved to results/
```

---

## Section A: The Dark Theme Setup

At the very top of `evaluate.py`, **before any plotting code**, the matplotlib defaults are set:

```python
import matplotlib
matplotlib.use("Agg")            # Must be BEFORE importing pyplot!
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",   # Deep navy background
    "axes.facecolor":   "#16213e",   # Slightly lighter navy
    "axes.edgecolor":   "#0f3460",   # Dark blue borders
    "text.color":       "#eaeaea",   # Light gray text
    "axes.labelcolor":  "#eaeaea",
    "xtick.color":      "#eaeaea",
    "ytick.color":      "#eaeaea",
    "grid.color":       "#0f3460",
    "grid.linestyle":   "--",
    "grid.alpha":       0.5,
    "font.family":      "sans-serif",
})

ACCENT  = "#e94560"   # Vivid red-pink — main data color
ACCENT2 = "#0f3460"   # Dark blue — histogram bars
GREEN   = "#06d6a0"   # Teal — perfect-fit line
YELLOW  = "#ffd166"   # Warm yellow — labels on bars
```

> **IMPORTANT:** `matplotlib.use("Agg")` **must** come before `import matplotlib.pyplot`. If you import pyplot first and then call `.use()`, you get a warning and the backend doesn't switch. The Agg backend renders to PNG files without needing a display.

**Why a dark theme?**
- Charts in research papers and hackathon reports look more professional
- Dark backgrounds make colorful data points pop visually
- It demonstrates intentional design choices — not defaults

---

## Section B: Loading Model and Reproducing the Test Split

### Step 7.1: Load the saved model

```python
def load_model_and_features():
    model_path = MODELS_DIR / "best_model.pkl"
    feat_path  = MODELS_DIR / "feature_columns.json"

    if not model_path.exists():
        sys.exit("[ERR] Model not found. Run: python models/train.py")

    model     = joblib.load(model_path)
    info      = json.loads(feat_path.read_text())
    columns   = info.get("columns", [])
    best_name = info.get("best_model", "Best Model")

    return model, columns, best_name
```

### Step 7.2: Reproduce the exact same test split

```python
_, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
```

**CRITICAL:** The `random_state=42` here **must match** the one used in `train.py`. If they differ, you'd evaluate on rows that were also in the training set — which would give artificially inflated metrics (the model has "seen" those examples).

Using the same seed guarantees `X_test` here is **identical** to `X_test` in `train.py`.

---

## Section C: Computing Metrics

```python
def compute_metrics(y_true, y_pred) -> dict:
    err  = np.abs(y_true.values - y_pred)      # Error for each sample
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = math.sqrt(mean_squared_error(y_true, y_pred))
    acc1 = float(np.mean(err <= 1) * 100)       # % predictions within +-1
    acc2 = float(np.mean(err <= 2) * 100)       # % predictions within +-2

    return {
        "MAE":               round(mae, 3),
        "RMSE":              round(rmse, 3),
        "Accuracy_within_1": round(acc1, 1),
        "Accuracy_within_2": round(acc2, 1),
        "Max_error":         int(err.max()),
        "Median_error":      round(float(np.median(err)), 2),
    }
```

### Interpreting Each Metric

**MAE (Mean Absolute Error)**
```
MAE = (|pred_1 - actual_1| + |pred_2 - actual_2| + ... + |pred_n - actual_n|) / n
```
- `MAE = 0.87` → on average, predictions are off by 0.87 gate levels
- **Target: < 2.0**

**RMSE (Root Mean Squared Error)**
```
RMSE = sqrt( mean( (pred - actual)^2 ) )
```
- Penalizes large errors more heavily than MAE
- If RMSE >> MAE, there are a few very bad predictions
- **Target: < 3.0**

**±1 Accuracy**
```
Acc1 = (number of predictions where |pred - actual| <= 1) / total × 100%
```
- "What % of predictions are within 1 gate level of truth?"
- **Target: > 75%** (this is the primary hackathon metric)
- **Our achievement: ~83%**

**±2 Accuracy**
- Same but within 2 gate levels
- **Target: > 90%**

---

## Section D: The 3 Plots

### Plot 1: Actual vs. Predicted Scatter Plot

```python
def plot_actual_vs_predicted(y_true, y_pred, model_name: str):
    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#1a1a2e")
    ax.set_facecolor("#16213e")

    # Scatter: each point is one test sample
    ax.scatter(y_true, y_pred, alpha=0.6, s=40,
               color=ACCENT, edgecolors="none", label="Predictions")

    # Perfect-fit diagonal: if pred == actual, all points lie here
    lo, hi = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    ax.plot([lo, hi], [lo, hi], color=GREEN, lw=2, ls="--", label="Perfect fit")

    # +-1 band: the acceptable zone
    ax.fill_between([lo, hi], [lo-1, hi-1], [lo+1, hi+1],
                    color=GREEN, alpha=0.1, label="+-1 depth band")
```

**How to read this chart:**
- Points close to the diagonal = accurate predictions
- Points inside the green band = within ±1 gate level (good!)
- Points far from the diagonal = large errors (investigate these!)

### Plot 2: Feature Importance Bar Chart

```python
def plot_feature_importance(model, feature_cols: list[str]):
    est = model
    if hasattr(model, "named_steps"):        # Unwrap Pipeline
        est = model.named_steps.get("model", model)

    if hasattr(est, "feature_importances_"):
        raw = est.feature_importances_
    else:
        print("  Feature importance not available for this model type.")
        return

    imp  = pd.Series(raw, index=feature_cols).sort_values(ascending=True)
    top  = imp.tail(15)   # Show top 15 most important
```

**Why unwrap the Pipeline?** `Pipeline` wraps the model. `model.feature_importances_` doesn't exist on a Pipeline, but `model.named_steps["model"].feature_importances_` does.

**What features are typically most important:**
1. `op_type_MUL` — multiplications are always deep
2. `signal_width` — wider = deeper for arithmetic
3. `op_complexity` — directly encodes circuit cost
4. `nesting_depth` — if/case adds MUX stages
5. `fanin` — more inputs = more logic

### Plot 3: Error Distribution Histogram

```python
def plot_error_distribution(errors: np.ndarray):
    bins = range(0, int(errors.max()) + 2)
    ax.hist(errors, bins=bins, color=ACCENT2, edgecolor=ACCENT, alpha=0.9)

    within1 = (errors <= 1).sum()
    ax.axvline(1.5, color=GREEN, ls="--", lw=2,
               label=f"+-1 boundary ({within1} samples)")
```

**How to read this chart:**
- Tall bar at error=0 → many exact predictions
- Bars at 1, 2 → close predictions
- Bars at 5, 10+ → problematic outliers — worth investigating

---

## Section E: Saving Results

```python
eval_path = RESULTS_DIR / "evaluation_metrics.json"
with open(eval_path, "w") as fh:
    json.dump({best_name: metrics}, fh, indent=2)
```

**The saved JSON looks like:**
```json
{
  "XGBoost": {
    "MAE": 0.872,
    "RMSE": 1.643,
    "Accuracy_within_1": 83.7,
    "Accuracy_within_2": 93.9,
    "Max_error": 8,
    "Median_error": 0.5
  }
}
```

This allows automatic CI/CD checks — a pipeline can verify metrics meet thresholds before deploying.

---

## Understanding Results: What If Accuracy Is Low?

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| MAE > 3.0 | Too few training samples | Add more .v files |
| Max_error > 15 | Outlier signals in data | Check the CSV for anomalies |
| ±1 Accuracy < 60% | Wrong model or features | Try adjusting XGBoost params |
| All predicted depths = same value | Label leak or degenerate data | Re-run extractor.py |

---

> **[<< Part 6: Training](./PART_06_TRAINING.md)** | **[Next: Inference >>](./PART_08_INFERENCE.md)**
