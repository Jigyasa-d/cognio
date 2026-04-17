from fastapi import APIRouter

router = APIRouter()

@router.post("/retention")
def retention():
    return {"logged": True}