
import base64
import os

import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

router = APIRouter()

MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class VisualSolutionResponse(BaseModel):
    answer: str


@router.post(
    "/visual/solve",
    response_model=VisualSolutionResponse,
)
async def solve_visual_question(
    file: UploadFile = File(...),
    question: str = Form(default=""),
):
    content_type = (file.content_type or "").lower()

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Upload a JPG, PNG or WEBP image.",
        )

    image_bytes = await file.read(MAX_IMAGE_BYTES + 1)

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The image is empty.",
        )

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Image must be 10 MB or smaller.",
        )

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    model = os.getenv(
        "OLLAMA_VISION_MODEL",
        "qwen2.5vl:3b",
    )

    base_url = os.getenv(
        "OLLAMA_BASE_URL",
        "http://ollama:11434",
    ).rstrip("/")

    system_prompt = """
You are Cognio, a visual learning assistant.

Read the uploaded image and solve the student's question.
The image may contain printed text, handwriting, equations,
graphs, charts, diagrams, labels, or mathematical figures.

Return a clear educational response with these sections:

QUESTION IDENTIFIED
Briefly state the question you understood.

EXPLANATION
Explain the method in student-friendly language.

STEP-BY-STEP SOLUTION
Give numbered steps with the necessary calculations.

FINAL ANSWER
State the final answer clearly, including units where relevant.

SIMILAR PRACTICE QUESTION
Create one similar question and include its answer.

Check calculations and units. Do not invent unreadable values
or diagram labels. If the image is unclear, state what needs
clarification instead of guessing.

Give a concise explanation of the solution rather than
unnecessary internal reasoning.
"""

    user_text = (
        "Solve the question shown in this image.\n"
        + (
            f"Additional instruction: {question.strip()}\n"
            if question.strip()
            else ""
        )
        + "Explain the method, show the solution steps, "
        "give the final answer, and create one similar "
        "practice question with its answer."
    )

    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_text,
                "images": [image_base64],
            },
        ],
        "options": {
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=(10, 300),
        )

        if response.status_code == 404:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Model '{model}' was not found. "
                    f"Download it using: ollama pull {model}"
                ),
            )

        response.raise_for_status()

        data = response.json()
        answer = (
            data.get("message", {})
            .get("content", "")
            .strip()
        )

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="The local vision model returned an empty answer.",
            )

        return {"answer": answer}

    except HTTPException:
        raise

    except requests.exceptions.ConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Cannot connect to Ollama. Make sure the "
                "Ollama service is running and the model "
                "has been downloaded."
            ),
        ) from exc

    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                "The model took too long to respond. "
                "Try a smaller image or retry."
            ),
        ) from exc

    except requests.exceptions.RequestException as exc:
        print(
            f"Ollama solver error: "
            f"{type(exc).__name__}: {exc}"
        )
        raise HTTPException(
            status_code=502,
            detail="The local vision model could not process this image.",
        ) from exc
