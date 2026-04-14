from fastapi import FastAPI
from app.routers import events

app = FastAPI()

app.include_router(events.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok"}