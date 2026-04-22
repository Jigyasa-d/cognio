from fastapi import APIRouter

router = APIRouter()

@router.get("/analytics/{student_id}")
def analytics(student_id: str):
    return {"student_id": student_id, "status": "ok"}