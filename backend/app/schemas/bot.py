from pydantic import BaseModel


class BotRegisterRequest(BaseModel):
    telegram_id: int
    full_name: str
    phone: str
    section_id: int


class BotStopCardRequest(BaseModel):
    reporter_telegram_id: int
    violator_name: str
    section_id: int
    description: str


class ManagerTelegramResponse(BaseModel):
    telegram_id: int
    full_name: str

    model_config = {"from_attributes": True}
