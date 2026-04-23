from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🔴 EXPLICIT ROUTER IMPORTS (fix collision)
from app.routers.events import router as events_router
from app.routers.adapt import router as adapt_router
from app.routers.analytics import router as analytics_router
from app.routers.retention import router as retention_router

from app.models.db import Base, engine

# 🔴 IMPORT MODELS (for table creation)
from app.models import event, retention, content_library

# 🔴 CREATE TABLES
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔴 INCLUDE ROUTERS (fixed)
app.include_router(events_router, prefix="/api/v1")
app.include_router(adapt_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(retention_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}