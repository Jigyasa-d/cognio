from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

try:
    from ml.src.shap_explainer import get_top_features
except ImportError:
    from src.shap_explainer import get_top_features


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "xgb_full.joblib"


class CognioPredictor:
    def __init__(self, model_path: Path = MODEL_PATH):
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Run retrain.py first.")

        artifact = joblib.load(model_path)

        if not isinstance(artifact, dict) or "model" not in artifact or "feature_columns" not in artifact:
            raise ValueError("Saved model artifact format is invalid.")

        self.model = artifact["model"]
        self.feature_columns: List[str] = artifact["feature_columns"]

        self.inverse_label_map: Dict[int, str] = {
            int(k): v for k, v in artifact.get(
                "inverse_label_map",
                {0: "LOW", 1: "MODERATE", 2: "HIGH"},
            ).items()
        }

        self.explainer = shap.TreeExplainer(self.model)

    # ---------------- FEATURE ADAPTER ---------------- #
    def _adapt_live_to_training_features(self, live_features: Dict[str, float]) -> Dict[str, float]:
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

    # ---------------- PREDICTION ---------------- #
    def predict(self, live_features: Dict[str, float]) -> Dict:
        adapted = self._adapt_live_to_training_features(live_features)

        input_df = pd.DataFrame(
            [[adapted[col] for col in self.feature_columns]],
            columns=self.feature_columns,
        )

        probs = self.model.predict_proba(input_df)[0]
        pred_idx = int(np.argmax(probs))
        confidence = float(probs[pred_idx])
        strain_level = self.inverse_label_map[pred_idx]

        # ---------------- CALIBRATION ---------------- #

        # LOW confidence → MODERATE
        if confidence < 0.55:
            strain_level = "MODERATE"

        # HIGH override
        if adapted["incorrect_rate"] > 0.7 and adapted["avg_elapsed_time"] > 5:
            strain_level = "HIGH"

        # MODERATE ZONE (FIXED)
        elif (
            0.25 < adapted["incorrect_rate"] <= 0.7
            or 3 < adapted["avg_elapsed_time"] <= 6
            or adapted["retry_rate"] > 0.3
        ):
            strain_level = "MODERATE"

        # ---------------- EXPLANATION ---------------- #
        try:
            shap_values = self.explainer.shap_values(x_df)

            if isinstance(shap_values, list):
                shap_vals = shap_values[pred_idx][0]
            else:
                shap_vals = shap_values[0]

            feature_importance = dict(zip(self.feature_columns, shap_vals))

            top_features = sorted(
                feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]

            top_features = [f[0] for f in top_features]

        except Exception:
            top_features = sorted(
                {
                    "error_rate": adapted["incorrect_rate"],
                    "avg_elapsed_time": adapted["avg_elapsed_time"],
                    "retry_rate": adapted["retry_rate"],
                    "hint_reliance": live_features.get("hint_reliance", 0),
                }.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )[:3]

            top_features = [f[0] for f in top_features]

        trigger_adaptation = strain_level in {"HIGH", "MODERATE"}

        return {
            "strain_level": strain_level,
            "confidence": round(confidence, 4),
            "trigger_adaptation": trigger_adaptation,
            "top_features": top_features
        }