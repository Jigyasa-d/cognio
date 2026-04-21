from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "rf_prototype.joblib"
SCALER_PATH = ROOT / "models" / "scaler.joblib"

FEATURE_COLUMNS = [
    "n_interactions",
    "accuracy",
    "accuracy_pct",
    "incorrect_rate",
    "avg_elapsed_time",
    "median_elapsed_time",
    "std_elapsed_time",
    "p90_elapsed_time",
    "long_response_rate",
    "retry_rate",
    "wrong_streak_max",
    "efficiency_score",
    "error_burden",
    "retry_burden",
    "time_pressure_index",
    "struggle_index",
    "consistency_index",
    "pace_ratio",
    "elapsed_range_proxy",
]

LABEL_MAP = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
}


class CognioPredictor:
    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Missing model: {MODEL_PATH}")
        if not SCALER_PATH.exists():
            raise FileNotFoundError(f"Missing scaler: {SCALER_PATH}")

        self.model = joblib.load(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)

    def _adapt_live_to_training_features(self, live_features: dict) -> dict:
        latency_delta = float(live_features.get("latency_delta", 0.0))
        error_rate = float(live_features.get("error_rate", 0.0))
        attempt_burst = float(live_features.get("attempt_burst", 0.0))
        attention_drop = float(live_features.get("attention_drop", 0.0))
        hint_reliance = float(live_features.get("hint_reliance", 0.0))
        cold_start_latency = float(live_features.get("cold_start_latency", 0.0))
        exit_flag_ratio = float(live_features.get("exit_flag_ratio", 0.0))
        reread_normalized = float(live_features.get("reread_normalized", 0.0))

        n_interactions = 5.0
        accuracy = max(0.0, min(1.0, 1.0 - error_rate))
        accuracy_pct = accuracy * 100.0

        avg_elapsed_time = max(0.0, cold_start_latency / 1000.0)
        median_elapsed_time = max(0.0, avg_elapsed_time * 0.9)
        std_elapsed_time = max(0.0, latency_delta / 1000.0)
        p90_elapsed_time = max(avg_elapsed_time, avg_elapsed_time + std_elapsed_time)

        long_response_rate = max(0.0, min(1.0, attention_drop * 0.4 + attempt_burst * 0.6))
        retry_rate = max(0.0, min(1.0, attempt_burst * 0.7 + hint_reliance * 0.3))
        wrong_streak_max = max(0.0, min(5.0, round(error_rate * 5)))

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

        return {
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

    def predict(self, live_features: dict) -> dict:
        adapted = self._adapt_live_to_training_features(live_features)

        row = pd.DataFrame([[adapted[col] for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
        row_scaled = self.scaler.transform(row)

        probs = self.model.predict_proba(row_scaled)[0]
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        strain_level = LABEL_MAP[pred_idx]

        if confidence < 0.5:
            strain_level = "MODERATE"

        importances = self.model.feature_importances_
        contribution_scores = np.abs(importances * row_scaled[0])
        top_idx = np.argsort(contribution_scores)[::-1][:3]
        top_features = [FEATURE_COLUMNS[i] for i in top_idx]

        trigger_adaptation = strain_level in {"HIGH", "MODERATE"}

        return {
            "strain_level": strain_level,
            "confidence": round(confidence, 4),
            "top_features": top_features,
            "trigger_adaptation": trigger_adaptation,
        }