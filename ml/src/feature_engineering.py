from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd


# -------------------------------------------------------------------
# Stage 1 / training feature columns from labeled session data
# -------------------------------------------------------------------
TRAINING_REQUIRED_COLUMNS = [
    "user_id",
    "session_num",
    "session_id",
    "n_interactions",
    "accuracy",
    "incorrect_rate",
    "avg_elapsed_time",
    "median_elapsed_time",
    "std_elapsed_time",
    "p90_elapsed_time",
    "long_response_rate",
    "retry_rate",
    "wrong_streak_max",
    "strain_score",
    "strain_level",
]


# -------------------------------------------------------------------
# Stage 3 / live rolling-window feature columns
# -------------------------------------------------------------------
FEATURE_COLUMNS = [
    "latency_delta",
    "error_rate",
    "attempt_burst",
    "attention_drop",
    "hint_reliance",
    "cold_start_latency",
    "exit_flag_ratio",
    "reread_normalized",
]

STAGE3_FEATURE_COLUMNS = [
    "latency_delta",
    "error_rate_window",
    "attempt_burst",
    "attention_drop",
    "hint_reliance",
    "cold_start_latency",
    "exit_flag_ratio",
    "reread_normalized",
]


# -------------------------------------------------------------------
# Shared helpers for Stage 3 event-based engineering
# -------------------------------------------------------------------
def _prepare_event_frame(
    events: List[Dict[str, Any]],
    content_length_words: int = 300,
) -> pd.DataFrame:
    df = pd.DataFrame(events).copy()

    defaults = {
        "student_id": "unknown_student",
        "content_id": "unknown_content",
        "timestamp": 0,
        "time_taken_ms": 0,
        "correct": 0,
        "scroll_depth": 100,
        "hint_count": 0,
        "reread_count": 0,
        "exit_flag": 0,
        "content_length_words": content_length_words,
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    numeric_cols = [
        "timestamp",
        "time_taken_ms",
        "correct",
        "scroll_depth",
        "hint_count",
        "reread_count",
        "exit_flag",
        "content_length_words",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(defaults[col])

    df["student_id"] = df["student_id"].astype(str)
    df["content_id"] = df["content_id"].astype(str)

    return df.sort_values(["student_id", "content_id", "timestamp"]).reset_index(drop=True)


def build_feature_vector(
    events: List[Dict[str, Any]],
    content_length_words: int = 300,
) -> Dict[str, float]:
    """
    Stage 1 helper:
    builds one aggregate feature vector for a session/group of events.
    """
    if not events:
        return {col: 0.0 for col in FEATURE_COLUMNS}

    df = _prepare_event_frame(events, content_length_words=content_length_words)

    latency_delta = 0.0
    if len(df) > 1:
        latency_delta = float(df["time_taken_ms"].diff().abs().fillna(0).mean())

    total_attempts = max(len(df), 1)
    error_rate = float((df["correct"] == 0).sum()) / total_attempts

    attempt_burst = 0.0
    if len(df) >= 4:
        ts = df["timestamp"].sort_values().to_list()
        if ts[-1] - ts[-4] <= 90000:
            attempt_burst = 1.0

    attention_drop = 0.0
    if len(df) > 1:
        scroll_diff = df["scroll_depth"].diff().fillna(0)
        attention_drop = 1.0 if (scroll_diff < -40).any() else 0.0

    hint_reliance = float(df["hint_count"].sum()) / total_attempts
    cold_start_latency = float(df.iloc[0]["time_taken_ms"])
    exit_flag_ratio = float(df["exit_flag"].sum()) / total_attempts

    last_content_len = (
        float(df["content_length_words"].iloc[-1]) if not df.empty else float(content_length_words)
    )
    reread_normalized = float(df["reread_count"].sum()) / max(last_content_len / 200.0, 1.0)

    return {
        "latency_delta": round(latency_delta, 4),
        "error_rate": round(error_rate, 4),
        "attempt_burst": round(attempt_burst, 4),
        "attention_drop": round(attention_drop, 4),
        "hint_reliance": round(hint_reliance, 4),
        "cold_start_latency": round(cold_start_latency, 4),
        "exit_flag_ratio": round(exit_flag_ratio, 4),
        "reread_normalized": round(reread_normalized, 4),
    }


def heuristic_label(features: Dict[str, float], median_latency_delta: float = 2500.0) -> str:
    error_rate = features.get("error_rate", 0.0)
    latency_delta = features.get("latency_delta", 0.0)
    attempt_burst = features.get("attempt_burst", 0.0)

    if error_rate > 0.6 and latency_delta > (2 * median_latency_delta) and attempt_burst == 1:
        return "HIGH"

    if (0.35 <= error_rate <= 0.6) or (
        (1.5 * median_latency_delta) <= latency_delta <= (2 * median_latency_delta)
    ):
        return "MODERATE"

    return "LOW"


class FeatureEngineer:
    """
    Stage 3:
    Raw events -> rolling-window behavioral features
    per (student_id, content_id).
    """

    def __init__(self, window_size: int = 5, default_content_length_words: int = 300):
        self.window_size = window_size
        self.default_content_length_words = default_content_length_words

    def _prepare_events(self, events_df: pd.DataFrame) -> pd.DataFrame:
        return _prepare_event_frame(
            events_df.to_dict(orient="records"),
            content_length_words=self.default_content_length_words,
        )

    def latency_delta(self, window_df: pd.DataFrame) -> float:
        if len(window_df) <= 1:
            return 0.0
        return float(window_df["time_taken_ms"].diff().abs().fillna(0).mean())

    def error_rate_window(self, window_df: pd.DataFrame) -> float:
        total = max(len(window_df), 1)
        return float((window_df["correct"] == 0).sum()) / total

    def attempt_burst(self, window_df: pd.DataFrame) -> float:
        if len(window_df) < 4:
            return 0.0
        ts = window_df["timestamp"].sort_values().to_list()
        return 1.0 if (ts[-1] - ts[-4]) <= 90000 else 0.0

    def attention_drop(self, window_df: pd.DataFrame) -> float:
        if len(window_df) <= 1:
            return 0.0
        scroll_diff = window_df["scroll_depth"].diff().fillna(0)
        return 1.0 if (scroll_diff < -40).any() else 0.0

    def hint_reliance(self, window_df: pd.DataFrame) -> float:
        total = max(len(window_df), 1)
        return float(window_df["hint_count"].sum()) / total

    def cold_start_latency(self, window_df: pd.DataFrame) -> float:
        if window_df.empty:
            return 0.0
        return float(window_df.iloc[0]["time_taken_ms"])

    def exit_flag_ratio(self, window_df: pd.DataFrame) -> float:
        total = max(len(window_df), 1)
        return float(window_df["exit_flag"].sum()) / total

    def reread_normalized(self, window_df: pd.DataFrame) -> float:
        if window_df.empty:
            return 0.0
        content_length_words = float(window_df["content_length_words"].iloc[-1])
        return float(window_df["reread_count"].sum()) / max(content_length_words / 200.0, 1.0)

    def transform_window(self, window_df: pd.DataFrame) -> Dict[str, float]:
        return {
            "latency_delta": round(self.latency_delta(window_df), 4),
            "error_rate_window": round(self.error_rate_window(window_df), 4),
            "attempt_burst": round(self.attempt_burst(window_df), 4),
            "attention_drop": round(self.attention_drop(window_df), 4),
            "hint_reliance": round(self.hint_reliance(window_df), 4),
            "cold_start_latency": round(self.cold_start_latency(window_df), 4),
            "exit_flag_ratio": round(self.exit_flag_ratio(window_df), 4),
            "reread_normalized": round(self.reread_normalized(window_df), 4),
        }

    def transform_group(self, group_df: pd.DataFrame) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        group_df = group_df.sort_values("timestamp").reset_index(drop=True)

        for end_idx in range(len(group_df)):
            start_idx = max(0, end_idx - self.window_size + 1)
            window_df = group_df.iloc[start_idx : end_idx + 1].copy()

            features = self.transform_window(window_df)
            features["student_id"] = str(group_df.iloc[end_idx]["student_id"])
            features["content_id"] = str(group_df.iloc[end_idx]["content_id"])
            features["window_index"] = int(end_idx)
            features["window_start_event"] = int(start_idx)
            features["window_end_event"] = int(end_idx)
            features["window_event_count"] = int(len(window_df))
            features["last_timestamp"] = float(group_df.iloc[end_idx]["timestamp"])

            rows.append(features)

        return pd.DataFrame(rows)

    def transform(self, events_df: pd.DataFrame) -> pd.DataFrame:
        df = self._prepare_events(events_df)

        feature_frames = []
        for (_, _), group in df.groupby(["student_id", "content_id"], dropna=False):
            feature_frames.append(self.transform_group(group))

        if not feature_frames:
            return pd.DataFrame(
                columns=[
                    "student_id",
                    "content_id",
                    "window_index",
                    "window_start_event",
                    "window_end_event",
                    "window_event_count",
                    "last_timestamp",
                    *STAGE3_FEATURE_COLUMNS,
                ]
            )

        result = pd.concat(feature_frames, ignore_index=True)

        ordered_cols = [
            "student_id",
            "content_id",
            "window_index",
            "window_start_event",
            "window_end_event",
            "window_event_count",
            "last_timestamp",
            *STAGE3_FEATURE_COLUMNS,
        ]
        return result[ordered_cols]


# -------------------------------------------------------------------
# Stage 1 / training feature engineering from labeled sessions
# -------------------------------------------------------------------
def build_training_features(labeled_df: pd.DataFrame) -> pd.DataFrame:
    df = labeled_df.copy()

    missing = [col for col in TRAINING_REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns in labeled_sessions data: {missing}"
        )

    eps = 1e-6

    df["accuracy_pct"] = df["accuracy"] * 100.0
    df["efficiency_score"] = df["accuracy"] / (df["avg_elapsed_time"] + eps)
    df["error_burden"] = df["incorrect_rate"] * df["n_interactions"]
    df["retry_burden"] = df["retry_rate"] * df["n_interactions"]
    df["time_pressure_index"] = df["avg_elapsed_time"] * df["incorrect_rate"]

    df["struggle_index"] = (
        0.35 * df["incorrect_rate"]
        + 0.20 * df["retry_rate"]
        + 0.15 * df["long_response_rate"]
        + 0.15 * (df["wrong_streak_max"] / (df["n_interactions"] + eps))
        + 0.15 * df["strain_score"]
    )

    df["consistency_index"] = 1.0 / (1.0 + df["std_elapsed_time"])
    df["pace_ratio"] = df["p90_elapsed_time"] / (df["median_elapsed_time"] + eps)
    df["elapsed_range_proxy"] = df["p90_elapsed_time"] - df["median_elapsed_time"]

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    df[numeric_cols] = df[numeric_cols].fillna(0.0)

    label_map = {
        "LOW": 0,
        "MODERATE": 1,
        "HIGH": 2,
    }
    df["target"] = df["strain_level"].map(label_map)

    if df["target"].isna().any():
        bad = df.loc[df["target"].isna(), "strain_level"].unique().tolist()
        raise ValueError(f"Unexpected strain_level values found: {bad}")

    final_cols = [
        "user_id",
        "session_num",
        "session_id",
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
        "strain_score",
        "efficiency_score",
        "error_burden",
        "retry_burden",
        "time_pressure_index",
        "struggle_index",
        "consistency_index",
        "pace_ratio",
        "elapsed_range_proxy",
        "strain_level",
        "target",
    ]
    return df[final_cols].copy()


def load_input(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"{input_path} not found.")

    if input_path.suffix.lower() == ".parquet":
        return pd.read_parquet(input_path)

    if input_path.suffix.lower() == ".csv":
        return pd.read_csv(input_path)

    raise ValueError(f"Unsupported input format: {input_path.suffix}")


def save_features(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(output_path, index=False)
    except ImportError as exc:
        raise ImportError(
            "Saving parquet requires pyarrow. Install it with: python3 -m pip install pyarrow"
        ) from exc


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "labeled_sessions.parquet"
    output_path = project_root / "data" / "features.parquet"

    if not input_path.exists():
        raise FileNotFoundError(
            "Training feature engineering expects this file first:\n"
            "ml/data/labeled_sessions.parquet\n"
            "Run Stage 1 before running this script."
        )

    print(f"Loading labeled sessions from: {input_path}")
    labeled_df = load_input(input_path)

    print("Building training/session-level features...")
    features_df = build_training_features(labeled_df)

    save_features(features_df, output_path)

    print(f"Saved features to: {output_path}")
    print(f"Shape: {features_df.shape}")
    print("\nColumns:")
    print(features_df.columns.tolist())
    print("\nClass distribution:")
    print(features_df['strain_level'].value_counts())
    print("\nTarget distribution:")
    print(features_df['target'].value_counts().sort_index())


if __name__ == "__main__":
    main()