import os
from pathlib import Path

from openai import OpenAI

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.txt"

CONTENT_LIBRARY = {
    "UNIT_DEMO": {
        "title": "Photosynthesis",
        "text": (
            "Photosynthesis is the process by which plants convert sunlight, water, "
            "and carbon dioxide into glucose and oxygen."
        )
    }
}


def load_prompt() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text(encoding="utf-8")
    return (
        "You are Cognio, an adaptive learning companion. "
        "Rewrite explanations based on student behavior and predicted cognitive strain."
    )


def get_content(content_id: str) -> dict:
    return CONTENT_LIBRARY.get(content_id, CONTENT_LIBRARY["UNIT_DEMO"])


def transform_content(
    prediction: dict,
    explanation_note: str,
    content_id: str,
    behavior_summary: str,
    features: dict,
) -> str:
    strain = prediction.get("strain_level", "LOW")
    top_features = prediction.get("top_features", [])
    content = get_content(content_id)

    wrong_streak = features.get("wrong_streak", 0)
    hints_used = features.get("hints_used", 0)
    rereads = features.get("rereads", 0)
    avg_response_time = features.get("avg_response_time", 0)
    error_rate = features.get("error_rate", 0)
    total_attempts = features.get("total_attempts", 0)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in backend environment")

    client = OpenAI(api_key=api_key)
    system_prompt = load_prompt()

    style_hint = {
        "HIGH": "Use very short sentences. Be gentle, simple, and reassuring.",
        "MODERATE": "Be clear, structured, and supportive.",
        "LOW": "Be smooth, simple, and slightly deeper."
    }.get(strain, "Be clear and helpful.")

    user_prompt = f"""
You are generating adaptive lesson support for a learner.

Topic:
{content["title"]}

Original content:
{content["text"]}

Predicted strain:
{strain}

Behavior summary:
{behavior_summary}

Behavior values:
- wrong_streak = {wrong_streak}
- hints_used = {hints_used}
- rereads = {rereads}
- avg_response_time_ms = {avg_response_time}
- error_rate = {error_rate}
- total_attempts = {total_attempts}

Top behavioral signals:
{", ".join(top_features) if top_features else "none"}

Critical instruction:
Do NOT make this response depend only on strain.
Use the exact behavior pattern.

Behavior-specific adaptation rules:
- If wrong_streak is high and response time is fast, the learner is likely guessing or spiraling. Reset the explanation simply and directly.
- If hints_used is high, the learner needs more guided support and scaffolding.
- If rereads is high, the learner needs rephrasing and conceptual clarity.
- If response time is slow, the learner may be hesitating and needs gentler pacing.
- Two learners with the same strain must still get noticeably different wording and structure if their behaviors differ.

Output style:
HIGH:
- short and simple
- may use one analogy
- may use short steps if helpful

MODERATE:
- structured explanation
- one example if useful

LOW:
- easy paraphrase
- slightly deeper, still simple

Strict rules:
- school-level language only
- no markdown
- no JSON
- no headings
- no identical structure across runs
- do not mention strain, metrics, or model features directly
- do not use advanced biology terms not already in the original content

Style guidance:
{style_hint}

Return only the adapted explanation.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=1.0,
        max_tokens=180,
    )

    text = response.choices[0].message.content
    if not text or not text.strip():
        raise RuntimeError("OpenAI returned an empty adaptation")

    return text.strip()