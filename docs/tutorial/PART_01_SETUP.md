# Part 1 — Environment Setup

> **[<< Overview](./PART_00_OVERVIEW.md)** | **[Next: Project Structure >>](./PART_02_PROJECT_STRUCTURE.md)**

---

## What You Will Do in This Part

1. Check Python version
2. Clone / set up the project folder
3. Create a virtual environment
4. Install all dependencies
5. Verify the installation

---

## Step 1.1 — Check Your Python Version

Open your terminal (Command Prompt or PowerShell on Windows, Terminal on Mac/Linux).

```bash
python --version
```

**Expected output:**
```
Python 3.10.x   (or 3.11.x / 3.12.x)
```

> **IMPORTANT:** This project requires Python **3.10 or higher**.
> - If you see Python 2.x, you must install Python 3.
> - If `python` is not found, try `python3 --version`.
> - Download Python from: https://www.python.org/downloads/

---

## Step 1.2 — Navigate to Your Project Folder

Your project is already at `k:\project`. Open a terminal and navigate there:

```powershell
# Windows PowerShell
cd k:\project

# OR if using CMD
cd k:\project
```

**Verify you're in the right place:**
```bash
dir    # Windows
ls     # Mac/Linux
```

You should see these items:
```
predict.py
inference.py
requirements.txt
features/
src/
models/
data/
eval/
results/
docs/
```

---

## Step 1.3 — Create a Virtual Environment

A **virtual environment** is an isolated Python workspace. It keeps this project's packages separate from other Python projects on your system.

```bash
# Create the virtual environment (named "venv")
python -m venv venv
```

This creates a `venv/` folder in your project directory.

> **IMPORTANT — Why use venv?**
> Without it, installing packages with pip affects your entire system Python.
> This can break other projects. Always use a venv for each project.

---

## Step 1.4 — Activate the Virtual Environment

You must activate the venv **every time** you open a new terminal for this project.

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (CMD / Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

After activation, your prompt will change:
```
(venv) k:\project>
```

The `(venv)` prefix confirms the environment is active.

> **Common Mistake:** If you see errors like `ModuleNotFoundError: No module named 'numpy'`, it almost always means you forgot to activate the venv.

---

## Step 1.5 — Install All Dependencies

Now install the required libraries from `requirements.txt`:

```bash
pip install -r requirements.txt
```

**What this installs (you will see progress bars):**
```
numpy        >= 1.24   — numerical arrays
pandas       >= 2.0    — DataFrames for dataset handling
scikit-learn >= 1.3    — ML models (Linear, Tree, Forest, MLP)
xgboost      >= 2.0    — gradient boosting (best model)
matplotlib   >= 3.7    — plotting / charts
seaborn      >= 0.12   — prettier plots
joblib       >= 1.3    — saving/loading model files (.pkl)
requests     >= 2.31   — downloading RTL files from GitHub
```

This may take 1–3 minutes on first install.

---

## Step 1.6 — Verify the Installation

Run this quick check to make sure everything installed correctly:

```bash
python -c "import numpy, pandas, sklearn, xgboost, matplotlib, joblib; print('All OK!')"
```

**Expected output:**
```
All OK!
```

If you get an ImportError for any package, re-run:
```bash
pip install <package-name>
```

---

## Step 1.7 — Verify Project Files Are Accessible

```bash
python -c "from features.extractor import VerilogFeatureExtractor; print('Extractor imported OK')"
```

**Expected output:**
```
Extractor imported OK
```

If you get `ModuleNotFoundError`, make sure you are running from the **project root** (`k:\project`), not from inside a subdirectory.

---

## What to Keep in Mind

| Tip | Why |
|-----|-----|
| Always activate `venv` first | Packages are installed only inside venv |
| Run all commands from `k:\project` | The scripts use relative path detection |
| Python 3.10+ is required | f-string syntax and type hints need 3.10+ |
| XGBoost install can be slow | It's a C++ library — be patient |

---

## Checkpoint

At the end of this part, you should have:
- [x] Python 3.10+ confirmed
- [x] Virtual environment created and activated
- [x] All 8 packages installed without errors
- [x] Feature extractor importable

---

> **[<< Overview](./PART_00_OVERVIEW.md)** | **[Next: Project Structure >>](./PART_02_PROJECT_STRUCTURE.md)**
