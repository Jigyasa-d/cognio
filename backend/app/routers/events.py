from fastapi import APIRouter, HTTPException
from app.schemas.adapt import AdaptRequest
from app.services.ml_client import predict_strain
from app.services.gpt_adapter import transform_content

router = APIRouter()


def build_behavior_summary(features: dict) -> str:
    wrong_streak = features.get("wrong_streak", 0)
    total_attempts = features.get("total_attempts", 0)
    hints_used = features.get("hints_used", 0)
    rereads = features.get("rereads", 0)
    avg_response_time = features.get("avg_response_time", 0)
    error_rate = features.get("error_rate", 0)

    observations = []

    if wrong_streak >= 3:
        observations.append("The learner is making repeated wrong attempts in a short sequence.")
    elif wrong_streak == 2:
        observations.append("The learner has made multiple recent mistakes and may be losing confidence.")
    elif wrong_streak == 1:
        observations.append("The learner has started to make mistakes but is not fully stuck yet.")

    if hints_used >= 2:
        observations.append("The learner is depending on hints for support.")
    elif hints_used == 1:
        observations.append("The learner needed some support from a hint.")

    if rereads >= 2:
        observations.append("The learner is rereading the material multiple times.")
    elif rereads == 1:
        observations.append("The learner went back to reread the content once.")

    if avg_response_time >= 8000:
        observations.append("Responses are very slow, which may indicate hesitation or overload.")
    elif avg_response_time >= 5000:
        observations.append("Responses are somewhat slow, suggesting uncertainty.")
    elif avg_response_time <= 1500 and wrong_streak >= 2:
        observations.append("The learner is responding quickly but inaccurately, which may suggest confusion or guessing.")

    if error_rate >= 0.75:
        observations.append("The current accuracy is very low.")
    elif error_rate >= 0.4:
        observations.append("The learner is showing a moderate level of inaccuracy.")

    if total_attempts <= 2:
        observations.append("This is still an early part of the interaction.")
    else:
        observations.append("There is enough interaction history to adapt more specifically.")

    return " ".join(observations)


def build_explanation_note(prediction: dict, behavior_summary: str) -> str:
    top_features = prediction.get("top_features", [])
    if top_features:
        return (
            f"Adapted because of {', '.join(top_features)}. "
            f"Behavior observed: {behavior_summary}"
        )
    return f"Adapted based on learner behavior: {behavior_summary}"


@router.post("/events")
def handle_event(data: AdaptRequest):
    try:
        features = data.features.model_dump()
        behavior_summary = build_behavior_summary(features)

        prediction = predict_strain(
            data.student_id,
            data.content_id,
            features
        )

        explanation_note = build_explanation_note(prediction, behavior_summary)

        adaptation = transform_content(
            prediction=prediction,
            explanation_note=explanation_note,
            content_id=data.content_id,
            behavior_summary=behavior_summary,
            features=features,
        )

        return {
            "adapt": {
                "prediction": {
                    "strain_level": prediction.get("strain_level", "LOW"),
                    "confidence": float(prediction.get("confidence", 0.0)),
                    "trigger_adaptation": bool(prediction.get("trigger_adaptation", True)),
                    "top_features": list(prediction.get("top_features", [])),
                },
                "adaptation": adaptation,
                "explanation_note": explanation_note,
                "behavior_summary": behavior_summary,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptation pipeline failed: {str(e)}")