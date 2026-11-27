
from dotenv import load_dotenv

load_dotenv()

import os
import time
import secrets
import asyncio
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    events,
    adapt,
    analytics,
    retention,
    solver,
    quiz_generation,
    learning,
)

BETA_TOKEN = os.getenv("COGNIO_BETA_TOKEN", "").strip()

if not BETA_TOKEN:
    raise RuntimeError("COGNIO_BETA_TOKEN is not configured.")

app = FastAPI(
    title="Cognio Backend",
    version="1.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

ALLOWED_PATHS = {
    "/api/v1/visual/solve",
    "/api/v1/visual-quiz/generate",
    "/api/v1/learning/analyze",
    "/api/v1/learning/adapt",
    "/api/v1/learning/feedback",
    "/api/v1/learning/chat",
}

AI_PATHS = {
    "/api/v1/visual/solve",
    "/api/v1/visual-quiz/generate",
    "/api/v1/learning/adapt",
    "/api/v1/learning/chat",
}

MAX_BODY_SIZE = 12 * 1024 * 1024
request_history = defaultdict(deque)
ai_lock = asyncio.Lock()


@app.middleware("http")
async def protect_beta_api(request: Request, call_next):

    path = request.url.path

    if path == "/health" and request.method == "GET":
        return await call_next(request)

    if path not in ALLOWED_PATHS:
        return JSONResponse(
            status_code=403,
            content={"detail": "Endpoint unavailable in beta mode."},
        )

    if request.method != "POST":
        return JSONResponse(
            status_code=405,
            content={"detail": "Method not allowed."},
        )

    supplied_token = request.headers.get("X-Cognio-Token", "")

    if not secrets.compare_digest(
        supplied_token.encode("utf-8"),
        BETA_TOKEN.encode("utf-8"),
    ):
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing Cognio access token."},
        )

    content_length = request.headers.get("content-length")

    try:
        if content_length is None:
            return JSONResponse(
                status_code=411,
                content={"detail": "Content-Length required."},
            )

        size = int(content_length)

        if size < 0 or size > MAX_BODY_SIZE:
            return JSONResponse(
                status_code=413,
                content={"detail": "Request is too large."},
            )

    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid request size."},
        )

    category = "ai" if path in AI_PATHS else "learning"
    limit = 10 if category == "ai" else 120

    now = time.monotonic()
    history = request_history[category]

    while history and now - history[0] >= 60:
        history.popleft()

    if len(history) >= limit:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit reached. Please try again shortly."},
            headers={"Retry-After": "60"},
        )

    history.append(now)

    if path in AI_PATHS:
        if ai_lock.locked():
            return JSONResponse(
                status_code=503,
                content={"detail": "Cognio is busy. Please try again shortly."},
                headers={"Retry-After": "10"},
            )

        async with ai_lock:
            return await call_next(request)

    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://[a-p]{32}",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Cognio-Token"],
)

app.include_router(events.router, prefix="/api/v1", tags=["events"])
app.include_router(adapt.router, prefix="/api/v1", tags=["adapt"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(retention.router, prefix="/api/v1", tags=["retention"])
app.include_router(solver.router, prefix="/api/v1", tags=["visual-solver"])
app.include_router(learning.router, prefix="/api/v1", tags=["adaptive-learning"])
app.include_router(quiz_generation.router)


@app.get("/health")
def health():
    return {"status": "ok"}
