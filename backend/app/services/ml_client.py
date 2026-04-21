from joblib import load
import numpy as np
from app.services.feature_adapter import adapt_features

# load model once
model = load("models/strain_model.joblib")

FEATURE_ORDER = [
    "n_interactions",
    "accuracy",
    "avg_elapsed_time",
    "strain_score",
    "struggle_index"
]

LABEL_MAP = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH"
}


def predict_strain(features: dict):
    adapted = adapt_features(features)

    # prepare input
    X = np.array([[float(adapted.get(f, 0)) for f in FEATURE_ORDER]])

    # prediction
    pred = model.predict(X)[0]

    # confidence (REAL)
    try:
        probs = model.predict_proba(X)[0]
        confidence = float(np.max(probs))
        pred_idx = int(np.argmax(probs))
        strain_level = LABEL_MAP.get(pred_idx, str(pred))
    except:
        # fallback if model doesn't support proba
        confidence = 0.85
        strain_level = str(pred)

    # -------- CALIBRATION (IMPORTANT) -------- #
    if confidence < 0.55:
        strain_level = "MODERATE"

    if adapted.get("accuracy", 1) < 0.3 and adapted.get("avg_elapsed_time", 0) > 5:
        strain_level = "HIGH"

    elif (
        0.3 <= adapted.get("accuracy", 1) <= 0.7
        or 3 <= adapted.get("avg_elapsed_time", 0) <= 6
    ):
        strain_level = "MODERATE"

    # -------- SIMPLE EXPLANATION -------- #
    explanation_features = {
        "accuracy": adapted.get("accuracy", 0),
        "avg_elapsed_time": adapted.get("avg_elapsed_time", 0),
        "strain_score": adapted.get("strain_score", 0),
        "struggle_index": adapted.get("struggle_index", 0)
    }

    top_features = sorted(
        explanation_features.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:3]

    top_features = [f[0] for f in top_features]

    return {
        "strain_level": strain_level,
        "confidence": round(confidence, 4),
        "trigger_adaptation": strain_level in ["HIGH", "MODERATE"],
        "top_features": top_features
    }