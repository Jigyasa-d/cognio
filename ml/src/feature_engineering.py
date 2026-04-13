from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


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


def _safe_div(a: float, b: float) -> float:
    return float(a) / float(b) if b else 0.0


def build_feature_vector(events: List[Dict[str, Any]], content_length_words: int = 300) -> Dict[str, float]:
    """
    Convert a rolling batch of LMS events into the shared feature schema.
    Expected event fields can include:
    - time_taken_ms
    - correct (0/1 or True/False)
    - timestamp
    - scroll_depth
    - hint_count
    - reread_count
    - exit_flag
    """

    if not events:
        return {col: 0.0 for col in FEATURE_COLUMNS}

    df = pd.DataFrame(events).copy()

    for col, default in {
        "time_taken_ms": 0,
        "correct": 0,
        "scroll_depth": 100,
        "hint_count": 0,
        "reread_count": 0,
        "exit_flag": 0,
        "timestamp": 0,
    }.items():
        if col not in df.columns:
            df[col] = default

    df["time_taken_ms"] = pd.to_numeric(df["time_taken_ms"], errors="coerce").fillna(0)
    df["correct"] = pd.to_numeric(df["correct"], errors="coerce").fillna(0)
    df["scroll_depth"] = pd.to_numeric(df["scroll_depth"], errors="coerce").fillna(100)
    df["hint_count"] = pd.to_numeric(df["hint_count"], errors="coerce").fillna(0)
    df["reread_count"] = pd.to_numeric(df["reread_count"], errors="coerce").fillna(0)
    df["exit_flag"] = pd.to_numeric(df["exit_flag"], errors="coerce").fillna(0)

    latency_delta = 0.0
    if len(df) > 1:
        latency_delta = float(df["time_taken_ms"].diff().abs().fillna(0).mean())

    total_attempts = max(len(df), 1)
    error_rate = float((df["correct"] == 0).sum()) / total_attempts

    # attempt burst: >3 attempts in last 90s
    attempt_burst = 0.0
    if "timestamp" in df.columns and len(df) >= 4:
        ts = pd.to_numeric(df["timestamp"], errors="coerce").fillna(0).sort_values().to_list()
        if ts[-1] - ts[max(0, len(ts) - 4)] <= 90000:
            attempt_burst = 1.0

    attention_drop = 0.0
    if len(df) > 1:
        scroll_diff = df["scroll_depth"].diff().fillna(0)
        attention_drop = 1.0 if (scroll_diff < -40).any() else 0.0

    hint_reliance = float(df["hint_count"].sum()) / total_attempts
    cold_start_latency = float(df.iloc[0]["time_taken_ms"])
    exit_flag_ratio = float(df["exit_flag"].sum()) / total_attempts
    reread_normalized = float(df["reread_count"].sum()) / max(content_length_words / 200.0, 1.0)

    features = {
        "latency_delta": round(latency_delta, 4),
        "error_rate": round(error_rate, 4),
        "attempt_burst": round(attempt_burst, 4),
        "attention_drop": round(attention_drop, 4),
        "hint_reliance": round(hint_reliance, 4),
        "cold_start_latency": round(cold_start_latency, 4),
        "exit_flag_ratio": round(exit_flag_ratio, 4),
        "reread_normalized": round(reread_normalized, 4),
    }

    return features


def heuristic_label(features: Dict[str, float], median_latency_delta: float = 2500.0) -> str:
    """
    Proxy label strategy from PRD:
    HIGH: error_rate > 0.6 AND latency_delta > 2x median AND attempt_burst = 1
    MODERATE: error_rate 0.35-0.6 OR latency_delta 1.5x-2x median
    LOW: else
    """
    error_rate = features.get("error_rate", 0.0)
    latency_delta = features.get("latency_delta", 0.0)
    attempt_burst = features.get("attempt_burst", 0.0)

    if error_rate > 0.6 and latency_delta > (2 * median_latency_delta) and attempt_burst == 1:
        return "HIGH"

    if (0.35 <= error_rate <= 0.6) or ((1.5 * median_latency_delta) <= latency_delta <= (2 * median_latency_delta)):
        return "MODERATE"

    return "LOW"