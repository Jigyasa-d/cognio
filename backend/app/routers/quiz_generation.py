import os
import re
import json
import base64
import logging

import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("cognio.quiz")

router = APIRouter(prefix="/api/v1/visual-quiz", tags=["Visual Quiz"])

# docker-compose sets OLLAMA_BASE_URL=http://ollama:11434 and OLLAMA_VISION_MODEL.
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/") + "/api/generate"
MODEL_NAME = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:3b")
MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
LEVELS = ("easy", "medium", "hard")

LEVEL_GUIDE = {
    "easy": "Test recall and basic understanding of facts stated in the image.",
    "medium": "Test relationships, interpretation and application of what the image says.",
    "hard": "Test deeper reasoning, comparisons and implications based on the image.",
}


class MCQ(BaseModel):
    question: str
    options: list[str]
    answer: str
    explanation: str = ""


class ConceptualQuestion(BaseModel):
    question: str
    answer: str
    explanation: str = ""


class DifficultyQuestions(BaseModel):
    mcqs: list[MCQ]
    conceptual: list[ConceptualQuestion]


class QuizResponse(BaseModel):
    easy: DifficultyQuestions
    medium: DifficultyQuestions
    hard: DifficultyQuestions


def build_prompt(level: str) -> str:
    return f"""You are Cognio's educational quiz generator.

Read the uploaded image carefully. It may be a textbook page, a printed
document, or handwritten notes.

Create {level.upper()} difficulty questions ONLY from content you can actually
read in the image. {LEVEL_GUIDE[level]}
Do not invent facts. If the image is mostly unreadable, return
{{"error": "Please upload a clearer image."}} and nothing else.

Return valid JSON only, in exactly this structure:

{{
  "mcqs": [
    {{
      "question": "Question text",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "answer": "Exact text of the correct option",
      "explanation": "Brief explanation based on the image"
    }}
  ],
  "conceptual": [
    {{
      "question": "Open-ended question",
      "answer": "Expected answer",
      "explanation": "Brief explanation"
    }}
  ]
}}

Rules:
- Exactly 3 mcqs and 2 conceptual questions.
- Each MCQ has exactly 4 distinct options and one correct answer.
- "answer" must be copied exactly from one of the 4 options.
- Conceptual questions are open-ended, not multiple choice.
- Keep technical terms and equations as written in the image.
"""


def extract_json(text: str) -> dict:
    """Parse model output, tolerating code fences or stray text around the JSON."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


def clean_mcq(raw) -> dict | None:
    """Return a valid MCQ dict, or None if it cannot be repaired."""
    if not isinstance(raw, dict):
        return None
    question = str(raw.get("question", "")).strip()
    options = raw.get("options")
    if not question or not isinstance(options, list):
        return None

    options = [str(o).strip() for o in options if str(o).strip()]
    options = list(dict.fromkeys(options))[:4]          # drop duplicates
    if len(options) != 4:
        return None

    answer = str(raw.get("answer", "")).strip()
    chosen = None
    if answer in options:
        chosen = answer
    else:
        for opt in options:                              # case-insensitive match
            if opt.lower() == answer.lower():
                chosen = opt
                break
        if chosen is None and re.fullmatch(r"[A-Da-d][\).:]?", answer):
            chosen = options["ABCD".index(answer[0].upper())]   # "B" -> 2nd option
        if chosen is None:
            for opt in options:                          # loose containment match
                if answer and (answer.lower() in opt.lower() or opt.lower() in answer.lower()):
                    chosen = opt
                    break
    if chosen is None:
        return None

    return {
        "question": question,
        "options": options,
        "answer": chosen,
        "explanation": str(raw.get("explanation", "")).strip(),
    }


def clean_conceptual(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    question = str(raw.get("question", "")).strip()
    answer = str(raw.get("answer", "")).strip()
    if not question or not answer:
        return None
    return {
        "question": question,
        "answer": answer,
        "explanation": str(raw.get("explanation", "")).strip(),
    }


async def generate_level(client: httpx.AsyncClient, image_b64: str, level: str) -> dict:
    payload = {
        "model": MODEL_NAME,
        "prompt": build_prompt(level),
        "images": [image_b64],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_ctx": 8192, "num_predict": 2048},
    }

    last_problem = "unknown"
    for attempt in (1, 2):                               # one automatic retry
        response = await client.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        raw_output = response.json().get("response", "")
        try:
            data = extract_json(raw_output)
        except (json.JSONDecodeError, ValueError):
            last_problem = "invalid JSON"
            logger.warning("%s attempt %d: invalid JSON: %.200s", level, attempt, raw_output)
            continue

        if isinstance(data, dict) and data.get("error"):
            raise HTTPException(status_code=422, detail=str(data["error"]))

        mcqs = [m for m in (clean_mcq(x) for x in (data.get("mcqs") or [])) if m]
        conceptual = [c for c in (clean_conceptual(x) for x in (data.get("conceptual") or [])) if c]
        if mcqs or conceptual:
            return {"mcqs": mcqs, "conceptual": conceptual}
        last_problem = "no usable questions"
        logger.warning("%s attempt %d: no usable questions", level, attempt)

    logger.error("Giving up on %s level: %s", level, last_problem)
    return {"mcqs": [], "conceptual": []}


@router.post("/generate", response_model=QuizResponse)
async def generate_visual_quiz(file: UploadFile = File(...)):
    if (file.content_type or "").lower() not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG, or WEBP image.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Image is too large. Maximum size is 10 MB.")

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        quiz: dict = {}
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0)) as client:
            for level in LEVELS:                         # 3 small requests are more reliable than 1 huge one
                quiz[level] = await generate_level(client, image_b64, level)

        if not any(quiz[l]["mcqs"] or quiz[l]["conceptual"] for l in LEVELS):
            raise HTTPException(
                status_code=502,
                detail="The model could not produce a valid quiz from this image. Try a clearer image.",
            )
        return QuizResponse.model_validate(quiz)

    except HTTPException:
        raise
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama at {OLLAMA_URL}. Check that the ollama container is running.",
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Quiz generation timed out. Try a smaller image.")
    except httpx.HTTPStatusError as exc:
        body = exc.response.text[:300]
        hint = " Pull the model: docker exec cognio-ollama ollama pull " + MODEL_NAME if exc.response.status_code == 404 else ""
        raise HTTPException(status_code=502, detail=f"Local model request failed: {body}{hint}")
    except Exception as exc:                             # keeps CORS headers on the response
        logger.exception("Unexpected quiz generation error")
        raise HTTPException(status_code=500, detail=f"Quiz generation error: {type(exc).__name__}: {exc}")