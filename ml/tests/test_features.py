import pandas as pd

from src.feature_engineering import (
    FeatureEngineer,
    build_feature_vector,
    heuristic_label,
)


def test_build_feature_vector():
    events = [
        {
            "student_id": "s1",
            "content_id": "c1",
            "time_taken_ms": 2000,
            "correct": 0,
            "scroll_depth": 100,
            "hint_count": 1,
            "reread_count": 1,
            "exit_flag": 0,
            "timestamp": 1000,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "time_taken_ms": 6000,
            "correct": 0,
            "scroll_depth": 50,
            "hint_count": 1,
            "reread_count": 2,
            "exit_flag": 0,
            "timestamp": 2000,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "time_taken_ms": 9000,
            "correct": 0,
            "scroll_depth": 30,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 1,
            "timestamp": 3000,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "time_taken_ms": 10000,
            "correct": 1,
            "scroll_depth": 20,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 0,
            "timestamp": 3500,
            "content_length_words": 400,
        },
    ]

    features = build_feature_vector(events, content_length_words=400)

    assert "error_rate" in features
    assert "latency_delta" in features
    assert features["error_rate"] == 0.75
    assert features["attention_drop"] == 1.0


def test_heuristic_label():
    features = {
        "latency_delta": 7000,
        "error_rate": 0.8,
        "attempt_burst": 1,
    }
    label = heuristic_label(features, median_latency_delta=2500)
    assert label == "HIGH"


def test_transform_window_returns_all_stage3_features():
    engineer = FeatureEngineer(window_size=5)

    events = [
        {
            "student_id": "s1",
            "content_id": "c1",
            "timestamp": 1000,
            "time_taken_ms": 2000,
            "correct": 0,
            "scroll_depth": 100,
            "hint_count": 1,
            "reread_count": 1,
            "exit_flag": 0,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "timestamp": 2000,
            "time_taken_ms": 6000,
            "correct": 0,
            "scroll_depth": 50,
            "hint_count": 1,
            "reread_count": 2,
            "exit_flag": 0,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "timestamp": 3000,
            "time_taken_ms": 9000,
            "correct": 0,
            "scroll_depth": 30,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 1,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "timestamp": 3500,
            "time_taken_ms": 10000,
            "correct": 1,
            "scroll_depth": 20,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 0,
            "content_length_words": 400,
        },
        {
            "student_id": "s1",
            "content_id": "c1",
            "timestamp": 4000,
            "time_taken_ms": 11000,
            "correct": 0,
            "scroll_depth": 10,
            "hint_count": 3,
            "reread_count": 4,
            "exit_flag": 1,
            "content_length_words": 400,
        },
    ]

    window_df = pd.DataFrame(events)
    features = engineer.transform_window(window_df)

    expected_keys = {
        "latency_delta",
        "error_rate_window",
        "attempt_burst",
        "attention_drop",
        "hint_reliance",
        "cold_start_latency",
        "exit_flag_ratio",
        "reread_normalized",
    }

    assert set(features.keys()) == expected_keys
    assert features["error_rate_window"] == 0.8
    assert features["attempt_burst"] == 1.0
    assert features["attention_drop"] == 1.0
    assert features["cold_start_latency"] == 2000.0


def test_transform_applies_rolling_windows_per_student_per_content():
    engineer = FeatureEngineer(window_size=5)

    df = pd.DataFrame(
        [
            {"student_id": "s1", "content_id": "c1", "timestamp": 1, "time_taken_ms": 1000, "correct": 1},
            {"student_id": "s1", "content_id": "c1", "timestamp": 2, "time_taken_ms": 2000, "correct": 0},
            {"student_id": "s1", "content_id": "c1", "timestamp": 3, "time_taken_ms": 3000, "correct": 0},
            {"student_id": "s1", "content_id": "c1", "timestamp": 4, "time_taken_ms": 4000, "correct": 1},
            {"student_id": "s1", "content_id": "c1", "timestamp": 5, "time_taken_ms": 5000, "correct": 1},
            {"student_id": "s1", "content_id": "c1", "timestamp": 6, "time_taken_ms": 6000, "correct": 0},
        ]
    )

    result = engineer.transform(df)

    assert len(result) == 6
    assert result.iloc[0]["window_event_count"] == 1
    assert result.iloc[4]["window_event_count"] == 5
    assert result.iloc[5]["window_event_count"] == 5
    assert result.iloc[5]["window_start_event"] == 1
    assert result.iloc[5]["window_end_event"] == 5


def test_transform_handles_missing_optional_columns():
    engineer = FeatureEngineer(window_size=5)

    df = pd.DataFrame(
        [
            {"student_id": "s1", "content_id": "c1", "timestamp": 1, "time_taken_ms": 1000, "correct": 1},
            {"student_id": "s1", "content_id": "c1", "timestamp": 2, "time_taken_ms": 2000, "correct": 0},
        ]
    )

    result = engineer.transform(df)

    assert len(result) == 2
    assert "hint_reliance" in result.columns
    assert "reread_normalized" in result.columns
    assert result.iloc[0]["hint_reliance"] == 0.0