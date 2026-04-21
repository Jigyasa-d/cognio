from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, adapt, analytics, retention
from app.models.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ CORS FIX (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(events.router, prefix="/api/v1")
app.include_router(adapt.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(retention.router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}