from src.feature_engineering import build_feature_vector, heuristic_label


def test_build_feature_vector():
    events = [
        {
            "time_taken_ms": 2000,
            "correct": 0,
            "scroll_depth": 100,
            "hint_count": 1,
            "reread_count": 1,
            "exit_flag": 0,
            "timestamp": 1000,
        },
        {
            "time_taken_ms": 6000,
            "correct": 0,
            "scroll_depth": 50,
            "hint_count": 1,
            "reread_count": 2,
            "exit_flag": 0,
            "timestamp": 2000,
        },
        {
            "time_taken_ms": 9000,
            "correct": 0,
            "scroll_depth": 30,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 1,
            "timestamp": 3000,
        },
        {
            "time_taken_ms": 10000,
            "correct": 1,
            "scroll_depth": 20,
            "hint_count": 2,
            "reread_count": 3,
            "exit_flag": 0,
            "timestamp": 3500,
        },
    ]

    features = build_feature_vector(events, content_length_words=400)

    assert "error_rate" in features
    assert "latency_delta" in features
    assert features["error_rate"] >= 0.0


def test_heuristic_label():
    features = {
        "latency_delta": 7000,
        "error_rate": 0.8,
        "attempt_burst": 1,
    }
    label = heuristic_label(features, median_latency_delta=2500)
    assert label == "HIGH"