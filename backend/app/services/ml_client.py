from joblib import load
import numpy as np
from app.services.feature_adapter import adapt_features

model = load("models/strain_model.joblib")

FEATURE_ORDER = [
    "n_interactions",
    "accuracy",
    "avg_elapsed_time",
    "strain_score",
    "struggle_index"
]

def predict_strain(features: dict):
    adapted = adapt_features(features)

    X = np.array([[adapted[f] for f in FEATURE_ORDER]])

    pred = model.predict(X)[0]

    return {
        "strain_level": pred,
        "confidence": 0.9,
        "trigger_adaptation": pred == "HIGH"
    }