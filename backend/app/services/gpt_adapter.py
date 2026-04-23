from openai import OpenAI
import os

client = OpenAI(api_key="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")

PROMPT_PATH = os.path.join("app", "prompts", "system_prompt.txt")


def load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def transform_content(prediction: dict, explanation_note: str) -> str:
    try:
        strain = prediction.get("strain_level", "LOW")

        system_prompt = load_prompt()

        content = "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into energy in the form of glucose."

        user_prompt = f"""
Strain Level: {strain}

Reason for adaptation:
{explanation_note}

Rewrite the following educational content:

Rules:
- HIGH → very simple
- MODERATE → clear + example
- LOW → detailed

Content:
{content}

Return only the rewritten explanation.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150,
            timeout=5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("LLM ERROR:", e)

        if strain == "HIGH":
            return "Plants use sunlight to make food."
        elif strain == "MODERATE":
            return "Plants use sunlight to create food for growth."
        else:
            return "Photosynthesis converts light energy into chemical energy."