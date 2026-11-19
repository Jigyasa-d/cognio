from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

from src.shap_explainer import get_top_features

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "xgb_full.joblib"


class CognioPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Run retrain.py first.")
        artifact = joblib.load(model_path)
        if not isinstance(artifact, dict) or "model" not in artifact or "feature_columns" not in artifact:
            raise ValueError("Saved XGBoost artifact format is invalid.")
        self.model = artifact["model"]
        self.feature_columns: List[str] = artifact["feature_columns"]
        self.inverse_label_map: Dict[int, str] = {
            int(k): v for k, v in artifact.get(
                "inverse_label_map", {0: "LOW", 1: "MODERATE", 2: "HIGH"}
            ).items()
        }

    def _adapt_live_to_training_features(self, live_features: Dict[str, float]) -> Dict[str, float]:
        """Map real rolling-session aggregates to the model's 19 training columns.

        Some training statistics (for example exact median and p90 latency) cannot be
        recovered from aggregates alone. Those fields are explicitly approximated from
        the mean and supplied latency spread rather than hardcoding five interactions.
        """
        get = lambda key, default=0.0: float(live_features.get(key, default) or 0.0)
        error_rate = float(np.clip(get("error_rate"), 0.0, 1.0))
        attempt_count = max(0.0, get("total_attempts"))
        n_interactions = max(attempt_count, 1.0)
        accuracy = 1.0 - error_rate
        accuracy_pct = accuracy * 100.0

        avg_ms = get("avg_response_time") or get("cold_start_latency")
        avg_elapsed_time = max(0.0, avg_ms / 1000.0)
        median_elapsed_time = avg_elapsed_time
        # The extension supplies the last response latency and the average; their
        # absolute difference is a conservative spread proxy, not a true stddev.
        latency_spread_ms = get("response_time_spread")
        if not latency_spread_ms:
            latency_spread_ms = abs(get("latency_delta") - avg_ms)
        std_elapsed_time = max(0.0, latency_spread_ms / 1000.0)
        p90_elapsed_time = max(avg_elapsed_time, avg_elapsed_time + std_elapsed_time)

        attention_drop = float(np.clip(get("attention_drop"), 0.0, 1.0))
        attempt_burst = float(np.clip(get("attempt_burst"), 0.0, 1.0))
        hint_reliance = float(np.clip(get("hint_reliance"), 0.0, 1.0))
        long_response_rate = attention_drop
        retry_rate = float(np.clip(0.7 * attempt_burst + 0.3 * hint_reliance, 0.0, 1.0))
        wrong_streak_max = float(np.clip(get("wrong_streak"), 0.0, 5.0))

        eps = 1e-6
        efficiency_score = accuracy / (avg_elapsed_time + eps)
        error_burden = error_rate * n_interactions
        retry_burden = retry_rate * n_interactions
        time_pressure_index = avg_elapsed_time * error_rate
        struggle_index = (
            0.35 * error_rate
            + 0.20 * retry_rate
            + 0.15 * long_response_rate
            + 0.15 * (wrong_streak_max / (n_interactions + eps))
            + 0.15 * hint_reliance
        )
        consistency_index = 1.0 / (1.0 + std_elapsed_time)
        pace_ratio = p90_elapsed_time / (median_elapsed_time + eps)
        elapsed_range_proxy = p90_elapsed_time - median_elapsed_time

        adapted = {
            "n_interactions": n_interactions,
            "accuracy": accuracy,
            "accuracy_pct": accuracy_pct,
            "incorrect_rate": error_rate,
            "avg_elapsed_time": avg_elapsed_time,
            "median_elapsed_time": median_elapsed_time,
            "std_elapsed_time": std_elapsed_time,
            "p90_elapsed_time": p90_elapsed_time,
            "long_response_rate": long_response_rate,
            "retry_rate": retry_rate,
            "wrong_streak_max": wrong_streak_max,
            "efficiency_score": efficiency_score,
            "error_burden": error_burden,
            "retry_burden": retry_burden,
            "time_pressure_index": time_pressure_index,
            "struggle_index": struggle_index,
            "consistency_index": consistency_index,
            "pace_ratio": pace_ratio,
            "elapsed_range_proxy": elapsed_range_proxy,
        }
        return adapted

    def predict(self, live_features: Dict[str, float]) -> Dict:
        adapted = self._adapt_live_to_training_features(live_features)
        input_df = pd.DataFrame(
            [[adapted[col] for col in self.feature_columns]],
            columns=self.feature_columns,
        )
        probs = self.model.predict_proba(input_df)[0]
        classes = getattr(self.model, "classes_", range(len(probs)))
        pred_class = int(classes[int(np.argmax(probs))])
        confidence = float(np.max(probs))
        strain_level = self.inverse_label_map.get(pred_class, "MODERATE")
        if confidence < 0.50:
            strain_level = "MODERATE"
        top_features = get_top_features(
            model=self.model,
            input_df=input_df,
            feature_columns=self.feature_columns,
            top_k=3,
        )
        return {
            "strain_level": strain_level,
            "confidence": round(confidence, 4),
            "top_features": top_features,
            "trigger_adaptation": strain_level in {"HIGH", "MODERATE"},
        }
