# 📚 RTL Combinational Depth Predictor — Complete Tutorial Series

> **A step-by-step guide to building an ML system that predicts chip timing from Verilog code**

---

## 🧭 What This Tutorial Covers

This tutorial walks you through building a **production-quality Machine Learning project** from scratch — end to end. You will build a system that reads Verilog (hardware description) files and **predicts how deep the combinational logic is**, which tells chip designers if their circuit will meet timing requirements — without running a slow synthesis tool.

---

## 🗺️ Tutorial Map

| Part | Title | What You Learn |
|------|-------|----------------|
| [Part 1](./PART_01_SETUP.md) | **Environment Setup** | Python venv, pip, project structure |
| [Part 2](./PART_02_PROJECT_STRUCTURE.md) | **Understanding the Project** | What every folder and file does |
| [Part 3](./PART_03_REQUIREMENTS.md) | **Dependencies Deep-Dive** | Why each library is needed |
| [Part 4](./PART_04_FEATURE_EXTRACTOR.md) | **Building the Feature Extractor** | Parsing Verilog with regex, 13 features |
| [Part 5](./PART_05_DATASET_PREP.md) | **Preparing the Dataset** | RTL data sources, CSV creation |
| [Part 6](./PART_06_TRAINING.md) | **Training ML Models** | 5 models, cross-validation, best-model selection |
| [Part 7](./PART_07_EVALUATION.md) | **Evaluating the Model** | MAE, RMSE, accuracy plots |
| [Part 8](./PART_08_INFERENCE.md) | **Making Predictions** | CLI, interactive, Python API |
| [Part 9](./PART_09_TIPS_AND_TRICKS.md) | **Pro Tips & Common Mistakes** | Debugging, Windows quirks, encoding issues |

---

## 🤔 Who Is This For?

- Students learning **applied ML on real engineering problems**
- Developers curious about **chip design (EDA/VLSI)**
- Anyone who wants to see how **regex-based feature engineering** works in practice
- People building **end-to-end ML pipelines** (data → features → train → evaluate → predict)

---

## 🧠 What Problem Are We Solving?

When engineers design chips (CPUs, GPUs, etc.), they write **Verilog code**. Before a chip can work at a target clock speed, all signals must "arrive" before the next clock tick. The number of **logic gates** a signal passes through is called its **combinational depth**.

Finding this depth normally requires running **synthesis** — a process that can take **hours**. Our ML model predicts the depth **in milliseconds**, from the source code alone.

```
Traditional Flow:          Our Flow:
Verilog → Synthesis        Verilog → Feature Extraction → ML Prediction
           (hours)                      (< 5 ms!)
```

---

## 🚀 Quick Summary of the Full Pipeline

```
Step 1: Setup Python environment + install dependencies
Step 2: Understand project structure
Step 3: Download/generate Verilog RTL files
Step 4: Run extractor.py  =>  extracts 13 features per signal  =>  dataset.csv
Step 5: Run train.py      =>  trains 5 ML models               =>  best_model.pkl
Step 6: Run evaluate.py   =>  computes MAE, RMSE, +-1 accuracy =>  saves plots
Step 7: Run predict.py    =>  give it a .v file + signal name  =>  depth prediction
```

---

## Start Here

Begin with **[Part 1 — Environment Setup](./PART_01_SETUP.md)**
