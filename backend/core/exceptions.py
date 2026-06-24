from fastapi import HTTPException


class BookingConflict(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=409, detail=message)


class SessionExpired(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(status_code=410, detail=message)


class N8nError(HTTPException):
    def __init__(self, message: str, upstream: str) -> None:
        super().__init__(status_code=502, detail=f"{message} (Upstream: {upstream})")
