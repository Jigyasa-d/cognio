from flask import Flask, jsonify, request

from predictor import CognioPredictor


app = Flask(__name__)
predictor = CognioPredictor()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": True})


@app.post("/ml/predict")
def predict():
    payload = request.get_json(silent=True) or {}

    student_id = payload.get("student_id")
    content_id = payload.get("content_id")
    features = payload.get("features", {})

    if not student_id or not content_id:
        return jsonify({"error": "student_id and content_id are required"}), 400

    if not isinstance(features, dict):
        return jsonify({"error": "features must be an object"}), 400

    result = predictor.predict(features)

    return jsonify(
        {
            "student_id": student_id,
            "content_id": content_id,
            **result,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)