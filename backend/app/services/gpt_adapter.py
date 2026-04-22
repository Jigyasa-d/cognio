from openai import OpenAI
import os

# 🔴 TEMP: hardcoded key (remove before submission)
client = OpenAI(api_key="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")

PROMPT_PATH = os.path.join("app", "prompts", "system_prompt.txt")


def load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def transform_content(prediction: dict) -> str:
    try:
        strain = prediction.get("strain_level", "LOW")

        system_prompt = load_prompt()

        # 🔥 REAL CONTENT (you can later replace this dynamically)
        content = "Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into energy in the form of glucose."

        # 🔥 STRONG INSTRUCTION PROMPT
        user_prompt = f"""
Strain Level: {strain}

Rewrite the following educational content based on the student's cognitive state:

Rules:
- HIGH → very simple, short sentences, easy words
- MODERATE → clear explanation with simple example
- LOW → detailed explanation with depth

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
            temperature=0.7,   # 🔥 improves variation
            max_tokens=150,
            timeout=5
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print("LLM ERROR:", e)

        # -------- FALLBACK -------- #
        if strain == "HIGH":
            return "Plants use sunlight to make food. This is called photosynthesis."
        elif strain == "MODERATE":
            return "Photosynthesis is how plants use sunlight to create food, helping them grow and survive."
        else:
            return "Photosynthesis is a biochemical process where plants convert sunlight into chemical energy stored as glucose."