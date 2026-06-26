# RTL Combinational Depth Predictor — Solution Summary

## Project Overview
ML model that predicts combinational logic depth of RTL signals without full synthesis.

**Team:** Girl Hackathon 2025 — Silicon Track  
**Track:** Silicon (EDA / Hardware Design)

---

## Problem Statement
Timing analysis via synthesis takes hours. This tool predicts combinational depth
in < 5ms directly from Verilog source, enabling early timing violation detection.

---

## Approach
### Data
- 56 local Verilog designs + open-source RTL (RTLLM, VTR, VerilogEval)
- 84 signal rows with 13 features each

### Features (13 per signal)
- Fan-in, fan-out, signal width, operator type, operator complexity
- Nesting depth, operation count, has_mul, has_add, in_loop, is_registered
- Module input count, conditional MUX count

### Models Compared
1. Linear Regression (baseline)
2. Decision Tree
3. Random Forest
4. **XGBoost** ← Best
5. MLP Neural Network

### Depth Labels
Analytical formulas based on standard EDA theory:
- Adders: 2·ceil(log2(w))  [CLA approximation]
- Multipliers: 3·ceil(log2(w)) + 2  [Wallace tree]
- Shifters: ceil(log2(w)) × 2  [barrel MUX stages]

---

## Results
| Metric              | Value   | Target  |
|---------------------|---------|---------|
| MAE                 | 0.235   | < 2.0   |
| RMSE                | 0.485   | < 3.0   |
| Accuracy within ±1  | **100%** | > 75%  |
| Accuracy within ±2  | **100%** | > 90%  |
| Inference time      | < 5 ms  | < 500ms |

---

## How to Run
```bash
pip install -r requirements.txt
python src/prepare_dataset.py
python src/train_models.py
python src/predict.py --file data/rtl_designs/local/simple_alu_8bit.v --signal result
```

---

## File Structure
```
src/
  auto_synth.py         Yosys automation
  parse_depth.py        Synthesis report parser
  feature_extraction.py 13-feature extractor
  prepare_dataset.py    Dataset pipeline
  train_models.py       5-model training
  save_model.py         Model export
  predict.py            Inference (CLI + API)
```
