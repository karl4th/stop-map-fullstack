from pydantic import BaseModel


class SectionCreate(BaseModel):
    name: str


class SectionUpdate(BaseModel):
    name: str


class SectionResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
