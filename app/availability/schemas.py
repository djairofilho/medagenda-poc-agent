from pydantic import BaseModel


class SlotBase(BaseModel):
    specialty: str
    slot_datetime: str


class SlotCreateRequest(BaseModel):
    slots: list[SlotBase]


class SlotResponse(SlotBase):
    id: int
    is_available: bool
    created_at: str


class SlotListResponse(BaseModel):
    total: int
    slots: list[SlotResponse]


class BulkDeleteRequest(BaseModel):
    ids: list[int]


class BulkActionResponse(BaseModel):
    affected_count: int
    message: str
