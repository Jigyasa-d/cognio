from fastapi import APIRouter
from app.schemas.events import EventRequest

router = APIRouter()

@router.post("/events")
def receive_event(data: EventRequest):
    print("EVENT RECEIVED:", data)
    return {
        "received": True,
        "queued_for_processing": True
    }