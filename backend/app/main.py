from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
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

app = FastAPI(title="Cognio Backend", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
