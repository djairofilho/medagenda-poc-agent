"""Existing availability HTTP contract."""

from fastapi import APIRouter, HTTPException, Request

from app.availability.schemas import (
    BulkActionResponse,
    BulkDeleteRequest,
    SlotCreateRequest,
    SlotListResponse,
)
from app.availability import service

router = APIRouter()


@router.get("/slots", response_model=SlotListResponse)
def get_slots(request: Request, specialty: str | None = None, date: str | None = None):
    try:
        slots = service.list_slots(request.app.state.session_factory, specialty, date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"total": len(slots), "slots": slots}


@router.post("/slots", response_model=BulkActionResponse)
def post_slots(payload: SlotCreateRequest, request: Request):
    try:
        count = service.create_slots(request.app.state.session_factory, [s.model_dump() for s in payload.slots])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"affected_count": count, "message": f"{count} slots created successfully"}


@router.delete("/slots", response_model=BulkActionResponse)
def remove_slots(payload: BulkDeleteRequest, request: Request):
    count = service.delete_slots(request.app.state.session_factory, payload.ids)
    return {"affected_count": count, "message": f"{count} slots deleted successfully"}
