import os
import requests

ML_PREDICT_URL = os.getenv("ML_SERVICE_URL", "http://ml:8001/ml/predict")


def predict_strain(student_id: str, content_id: str, features: dict):
    payload = {
        "student_id": student_id,
        "content_id": content_id,
        "features": features,
    }

    response = requests.post(ML_PREDICT_URL, json=payload, timeout=5)
    response.raise_for_status()
    return response.json()