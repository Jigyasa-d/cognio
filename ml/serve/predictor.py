from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np

from src.feature_engineering import FEATURE_COLUMNS


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "xgb_full.joblib"

LABELS = ["LOW", "MODERATE", "HIGH"]


class CognioPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Run retrain.py first.")
        self.model = joblib.load(model_path)

    def predict(self, features: Dict[str, float]) -> Dict:
        x = np.array([[float(features.get(col, 0.0)) for col in FEATURE_COLUMNS]])
        probs = self.model.predict_proba(x)[0]
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        strain_level = LABELS[pred_idx]

        feature_pairs = list(zip(FEATURE_COLUMNS, x[0]))
        feature_pairs.sort(key=lambda item: abs(item[1]), reverse=True)
        top_features: List[str] = [name for name, _ in feature_pairs[:3]]

        if confidence < 0.5:
            strain_level = "MODERATE"

        return {
            "strain_level": strain_level,
            "confidence": round(confidence, 4),
            "top_features": top_features,
            "trigger_adaptation": strain_level == "HIGH",
        }