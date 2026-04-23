from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


def _load_log(log_path: Path):
    if not log_path.exists():
        return []

    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "history" in data:
            return data["history"]
        return []
    except Exception:
        return []


def get_last_event(log_path: Path) -> Optional[dict]:
    history = _load_log(log_path)
    if not history:
        return None
    return history[-1]


def get_last_deployed_f1(log_path: Path) -> Optional[float]:
    last = get_last_event(log_path)
    if not last:
        return None
    value = last.get("deployed_f1")
    return float(value) if value is not None else None


def get_last_retrain_time(log_path: Path) -> Optional[datetime]:
    last = get_last_event(log_path)
    if not last:
        return None

    ts = last.get("timestamp")
    if not ts:
        return None

    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def schedule_due(log_path: Path, interval_days: int = 14) -> bool:
    last_time = get_last_retrain_time(log_path)
    if last_time is None:
        return True

    now = datetime.now(timezone.utc)
    return now - last_time >= timedelta(days=interval_days)


def f1_drop_exceeds_threshold(current_f1: float, baseline_f1: Optional[float], threshold: float = 0.05) -> bool:
    if baseline_f1 is None:
        return False
    if baseline_f1 <= 0:
        return False

    drop = (baseline_f1 - current_f1) / baseline_f1
    return drop > threshold


def should_retrain(
    current_f1: float,
    log_path: Path,
    interval_days: int = 14,
    drift_threshold: float = 0.05,
) -> tuple[bool, dict]:
    baseline_f1 = get_last_deployed_f1(log_path)
    due = schedule_due(log_path, interval_days=interval_days)
    drift = f1_drop_exceeds_threshold(current_f1, baseline_f1, threshold=drift_threshold)

    reasons = {
        "scheduled_due": due,
        "baseline_f1": baseline_f1,
        "current_f1": current_f1,
        "drift_triggered": drift,
        "drift_threshold": drift_threshold,
    }

    return (due or drift), reasons