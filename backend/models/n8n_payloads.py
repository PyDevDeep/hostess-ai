from pydantic import BaseModel


class CheckAvailabilityPayload(BaseModel):
    date: str
    time: str
    guests: int
    session_id: str


class ConfirmBookingPayload(BaseModel):
    date: str
    time: str
    guests: int
    name: str
    phone: str
    session_id: str


class AvailabilityResult(BaseModel):
    available: bool
    tables: list[str]
    message: str


class N8nBookingResponse(BaseModel):
    booking_id: str
    status: str
    message: str
