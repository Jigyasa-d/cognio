import os
import re
from pathlib import Path
from typing import List

from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "system_prompt.txt"


def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def preprocess_text(text: str) -> str:
    """
    Minimal NLP preprocessing that will NOT break the current pipeline.
    - normalizes whitespace
    - removes repeated spaces/newlines
    - keeps punctuation intact
    - truncates very long content safely
    """
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > 1200:
        text = text[:1200].rsplit(" ", 1)[0] + "..."

    return text


def extract_focus_terms(explanation_note: str) -> List[str]:
    """
    Very lightweight NLP-ish helper:
    converts explanation note into a small list of focus terms.
    """
    terms = re.findall(r"[A-Za-z_]+", explanation_note.lower())
    stopwords = {
        "adapted", "due", "to", "based", "on", "and", "the", "a", "an",
        "overall", "performance"
    }
    filtered = [t for t in terms if t not in stopwords]
    seen = []
    for t in filtered:
        if t not in seen:
            seen.append(t)
    return seen[:5]


def transform_content(prediction: dict, explanation_note: str) -> str:
    """
    Uses GPT-4o-mini to adapt content based on learner strain.
    Includes safe preprocessing + fallback if API fails.
    Keeps the same interface as your current code.
    """
    strain = prediction.get("strain_level", "LOW")

    system_prompt = load_prompt()

    # keeping your current content source so current flow does not break
    content = (
        "Photosynthesis is the process by which plants convert sunlight, "
        "water, and carbon dioxide into energy in the form of glucose."
    )

    # ✅ preprocessing step added safely
    content = preprocess_text(content)
    focus_terms = extract_focus_terms(explanation_note)

    user_prompt = f"""
Strain Level: {strain}

Reason for adaptation:
{explanation_note}

Focus terms:
{", ".join(focus_terms) if focus_terms else "general clarity"}

Rewrite the following educational content.

Rules:
- HIGH -> very simple, short sentences, step-by-step
- MODERATE -> clear explanation with one simple example
- LOW -> detailed but still easy to follow

Content:
{content}

Return only the rewritten explanation.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=180,
            timeout=8,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("LLM ERROR:", e)

        # safe fallback
        if strain == "HIGH":
            return "Plants use sunlight, water, and carbon dioxide to make their own food."
        elif strain == "MODERATE":
            return "Photosynthesis is how plants make food using sunlight, water, and carbon dioxide."
        else:
            return (
                "Photosynthesis is the biological process through which plants use sunlight "
                "to convert water and carbon dioxide into glucose and oxygen."
            )