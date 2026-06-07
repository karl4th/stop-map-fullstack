from datetime import datetime

from pydantic import BaseModel

from app.models.stop_card import StopCardStatus


class StopCardPhotoResponse(BaseModel):
    id: int
    minio_key: str
    photo_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class UserBriefResponse(BaseModel):
    id: int
    full_name: str

    model_config = {"from_attributes": True}


class StopCardResponse(BaseModel):
    id: int
    reporter_id: int
    reporter: UserBriefResponse | None = None
    violator_name: str
    violator_id: int | None = None
    violator: UserBriefResponse | None = None
    section_id: int
    description: str
    status: StopCardStatus

    acknowledged_by_id: int | None
    acknowledged_at: datetime | None
    acknowledged_by: UserBriefResponse | None = None

    fix_description: str | None
    fixed_by_id: int | None
    fixed_at: datetime | None
    fixed_by: UserBriefResponse | None = None

    safety_note: str | None
    safety_checked_by_id: int | None
    safety_checked_at: datetime | None
    safety_checked_by: UserBriefResponse | None = None

    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    photos: list[StopCardPhotoResponse] = []

    model_config = {"from_attributes": True}


class AcknowledgeRequest(BaseModel):
    pass


class SubmitFixRequest(BaseModel):
    fix_description: str


class SafetyDecisionRequest(BaseModel):
    note: str | None = None
