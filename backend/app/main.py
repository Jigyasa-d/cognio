from fastapi import FastAPI
from app.routers import events, adapt, analytics, retention

app = FastAPI()

app.include_router(events.router, prefix="/api/v1")
app.include_router(adapt.router)
app.include_router(analytics.router)
app.include_router(retention.router)


@app.get("/")
def root():
    return {"message": "Cognio backend is running"}