from fastapi import APIRouter
from app.services.gpt_adapter import generate_adaptive_response

router = APIRouter()

@router.post("/adapt")
def adapt():
    return generate_adaptive_response("sample content", "HIGH")