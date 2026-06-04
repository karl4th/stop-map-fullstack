from datetime import datetime

from pydantic import BaseModel

from app.models.stop_card import StopCardStatus


class StopCardPhotoResponse(BaseModel):
    id: int
    minio_key: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DisputeRequest(BaseModel):
    reason: str


class StopCardResponse(BaseModel):
    id: int
    reporter_id: int
    violator_name: str
    section_id: int
    description: str
    status: StopCardStatus
    dispute_reason: str | None
    created_at: datetime
    updated_at: datetime
    photos: list[StopCardPhotoResponse] = []

    model_config = {"from_attributes": True}
