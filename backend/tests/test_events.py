from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_event_batch_triggers_adapt(monkeypatch):
    def fake_predict_strain(student_id, content_id, features):
        return {
            "student_id": student_id,
            "content_id": content_id,
            "strain_level": "HIGH",
            "confidence": 0.91,
            "top_features": ["struggle_index", "p90_elapsed_time", "n_interactions"],
            "trigger_adaptation": True,
        }

    def fake_transform_content(prediction, explanation_note):
        return "Simplified explanation for struggling learner."

    monkeypatch.setattr("app.routers.adapt.predict_strain", fake_predict_strain)
    monkeypatch.setattr("app.routers.adapt.transform_content", fake_transform_content)

    payload = {
        "student_id": "STU_TEST",
        "content_id": "UNIT_TEST",
        "events": [
            {
                "timestamp": 1713850000.0,
                "features": {
                    "latency_delta": 4200,
                    "error_rate": 1.0,
                    "attempt_burst": 1,
                    "attention_drop": 0.3,
                    "hint_reliance": 0.2,
                    "cold_start_latency": 3000,
                    "exit_flag_ratio": 0.0,
                    "reread_normalized": 1.0,
                },
            },
            {
                "timestamp": 1713850001.0,
                "features": {
                    "latency_delta": 5100,
                    "error_rate": 1.0,
                    "attempt_burst": 2,
                    "attention_drop": 0.6,
                    "hint_reliance": 0.3,
                    "cold_start_latency": 3000,
                    "exit_flag_ratio": 0.0,
                    "reread_normalized": 1.0,
                },
            },
            {
                "timestamp": 1713850002.0,
                "features": {
                    "latency_delta": 5800,
                    "error_rate": 1.0,
                    "attempt_burst": 3,
                    "attention_drop": 0.8,
                    "hint_reliance": 0.4,
                    "cold_start_latency": 3000,
                    "exit_flag_ratio": 0.0,
                    "reread_normalized": 1.0,
                },
            },
        ],
    }

    response = client.post("/api/v1/events", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["stored"] is True
    assert "adapt" in body
    assert body["adapt"]["prediction"]["strain_level"] == "HIGH"
    assert body["adapt"]["prediction"]["top_features"] == [
        "struggle_index",
        "p90_elapsed_time",
        "n_interactions",
    ]
    assert body["adapt"]["adaptation"] == "Simplified explanation for struggling learner."