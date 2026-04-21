def adapt_features(live_features: dict):
    """
    Convert live event features → training features
    """

    latency = live_features.get("latency_delta", 0)
    error_rate = live_features.get("error_rate", 0)
    attempts = live_features.get("attempt_burst", 0)
    hints = live_features.get("hint_reliance", 0)

    # map to training-style features
    adapted = {
        "n_interactions": attempts + 1,
        "accuracy": 1 - error_rate,
        "avg_elapsed_time": latency,
        "strain_score": error_rate + (latency / 10000),
        "struggle_index": (error_rate * 0.6) + (hints * 0.4)
    }

    return adapted