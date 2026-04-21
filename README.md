# Cognio — Proactive Adaptive Learning System

Cognio is an AI-driven system that detects learner struggle in real time using behavioral signals and dynamically adapts explanations to improve understanding.

---

## 🚀 Overview

This project builds a complete end-to-end machine learning pipeline:

* Extracts behavioral patterns from EdNet dataset
* Generates session-level cognitive strain labels
* Trains an ML model to predict learner struggle
* Serves predictions via a FastAPI backend
* Adapts live user signals into model-ready features

---

## 🧠 Architecture

```
EdNet Dataset
    ↓
Stage 1: Session Construction + Labeling
    ↓
Stage 2: Feature Engineering
    ↓
Stage 3: Model Training (XGBoost)
    ↓
Live API (FastAPI)
    ↓
Feature Adapter (Live → Model Features)
    ↓
Strain Prediction + Adaptation Trigger
```

---

## 📊 Dataset Setup

This project uses the **EdNet-KT1 dataset**.

### Required Files

Place the following files in your local directory:

```
ml/data/raw/KT1/
- u1.csv
- u10.csv
- u100.csv

ml/data/raw/
- questions.csv
```

⚠️ Note: Raw dataset files are not included in the repository.

---

## ⚙️ Pipeline Execution

Run the full pipeline from inside the `ml/` directory:

```bash
python src/ednet_merge.py
python src/ednet_stage1.py
python src/feature_engineering.py
python src/retrain.py
```

This will:

* Merge raw data
* Generate labeled sessions
* Create training features
* Train and save the model

---

## 🤖 Run the API

Start the backend server:

```bash
python3 -m uvicorn serve.app:app --reload
```

Open in browser:

* Health check → http://127.0.0.1:8000/health
* API docs → http://127.0.0.1:8000/docs

---

## 🔮 Example Prediction Request

POST `/ml/predict`

```json
{
  "student_id": "STU_001",
  "content_id": "UNIT_1",
  "features": {
    "latency_delta": 3000,
    "error_rate": 0.6,
    "attempt_burst": 1.0,
    "attention_drop": 0.2,
    "hint_reliance": 0.4,
    "cold_start_latency": 5000,
    "exit_flag_ratio": 0.1,
    "reread_normalized": 0.3
  }
}
```

---

## 📈 Model Details

* Model: XGBoost Classifier
* Task: Multi-class classification (LOW / MODERATE / HIGH strain)
* Training data: Session-level behavioral features
* Evaluation: User-level split to avoid leakage

---

## ⚠️ Important Notes

* Labels are **pseudo-labeled** using behavioral heuristics
* Model performance reflects alignment with these heuristics
* Not a direct measure of true psychological cognitive strain

---

## 🎯 Key Features

* Behavioral signal analysis (time, errors, retries)
* Real-time strain detection
* Adaptive response triggering
* Clean ML pipeline design
* End-to-end system integration

---

## 👥 Team Workflow

* Raw datasets are shared manually or downloaded
* Model file can be reused without retraining
* Pipeline can be rerun for reproducibility

---

## 🧠 Summary

Cognio demonstrates how behavioral data can be transformed into actionable learning intelligence through a structured ML pipeline and real-time inference system.

---
