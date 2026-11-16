"""Domain errors of the Roomie service.

Every error has a stable, machine readable error code of the form
``ROOM-<http status>-<reason>``. Clients rely on these codes, so never change
an existing code - add a new one instead (see docs/error_codes.md).
"""

from fastapi import Request
from fastapi.responses import JSONResponse


class RoomieError(Exception):
    """Base class for all expected domain errors."""

    status_code: int = 400
    code: str = "ROOM-400-BAD-REQUEST"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(RoomieError):
    status_code = 401
    code = "ROOM-401-AUTH"


class PermissionDeniedError(RoomieError):
    status_code = 403
    code = "ROOM-403-FORBIDDEN"


class LateCancellationError(RoomieError):
    status_code = 403
    code = "ROOM-403-LATE-CANCEL"


class RoomNotFoundError(RoomieError):
    status_code = 404
    code = "ROOM-404-ROOM"


class BookingNotFoundError(RoomieError):
    status_code = 404
    code = "ROOM-404-BOOKING"


class BookingOverlapError(RoomieError):
    status_code = 409
    code = "ROOM-409-OVERLAP"


class BookingReleasedError(RoomieError):
    status_code = 410
    code = "ROOM-410-RELEASED"


class SlotAlignmentError(RoomieError):
    status_code = 422
    code = "ROOM-422-SLOT"


class DurationError(RoomieError):
    status_code = 422
    code = "ROOM-422-DURATION"


class BusinessHoursError(RoomieError):
    status_code = 422
    code = "ROOM-422-HOURS"


class AdvanceBookingError(RoomieError):
    status_code = 422
    code = "ROOM-422-ADVANCE"


class CapacityError(RoomieError):
    status_code = 422
    code = "ROOM-422-CAPACITY"


class BigRoomPolicyError(RoomieError):
    status_code = 422
    code = "ROOM-422-BIG-ROOM"


async def roomie_error_handler(request: Request, exc: RoomieError) -> JSONResponse:
    """Converts a RoomieError into the standard error response body.

    The body always has the shape ``{"error": {"code": ..., "message": ...}}``.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
