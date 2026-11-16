"""Domain models and API schemas of the Roomie service."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    EMPLOYEE = "employee"
    FACILITY_ADMIN = "facility_admin"


class User(BaseModel):
    user_id: str
    role: Role

    @property
    def is_admin(self) -> bool:
        return self.role == Role.FACILITY_ADMIN


class Room(BaseModel):
    room_id: str = Field(description="Short identifier, e.g. 'B2-14' (building B, floor 2, room 14).")
    name: str
    capacity: int = Field(gt=0)
    floor: int
    has_video: bool = False
    has_catering: bool = False


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CANCELLED = "cancelled"
    RELEASED = "released"  # automatically released after a no-show


# Bookings in these states block the room.
ACTIVE_STATUSES = {BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN}


class BookingCreate(BaseModel):
    """Request body for creating a booking."""

    room_id: str
    title: str = Field(min_length=1, max_length=120)
    start: datetime = Field(description="Timezone-aware start time.")
    end: datetime = Field(description="Timezone-aware end time.")
    attendees: int = Field(default=1, gt=0)


class Booking(BaseModel):
    booking_id: str
    room_id: str
    owner_id: str
    title: str
    start: datetime
    end: datetime
    attendees: int
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime
    cancelled_at: datetime | None = None
    checked_in_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES
