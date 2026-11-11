"""Endpoints for rooms and availability."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, Query

from roomie.auth import get_current_user, require_admin
from roomie.dependencies import get_availability_service, get_booking_service
from roomie.errors import RoomNotFoundError
from roomie.models import Room, User
from roomie.services.availability_service import AvailabilityService
from roomie.services.booking_service import BookingService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[Room])
def list_rooms(
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> list[Room]:
    return service.repository.list_rooms()


@router.get("/search", response_model=list[Room])
def search_rooms(
    start: datetime,
    end: datetime,
    attendees: int = Query(default=1, gt=0),
    needs_video: bool = False,
    user: User = Depends(get_current_user),
    availability: AvailabilityService = Depends(get_availability_service),
) -> list[Room]:
    """Finds free rooms for the given time range, smallest suitable room first."""
    return availability.find_rooms(start, end, attendees, needs_video)


@router.get("/{room_id}", response_model=Room)
def get_room(
    room_id: str,
    user: User = Depends(get_current_user),
    service: BookingService = Depends(get_booking_service),
) -> Room:
    room = service.repository.get_room(room_id)
    if room is None:
        raise RoomNotFoundError(f"Room {room_id} does not exist.")
    return room


@router.get("/{room_id}/availability")
def get_availability(
    room_id: str,
    day: date,
    user: User = Depends(get_current_user),
    availability: AvailabilityService = Depends(get_availability_service),
) -> list[dict]:
    """Returns the free slots of a room on a given day (office timezone)."""
    return [
        {"start": start.isoformat(), "end": end.isoformat()}
        for start, end in availability.free_slots(room_id, day)
    ]


@router.put("/{room_id}", response_model=Room)
def upsert_room(
    room_id: str,
    room: Room,
    admin: User = Depends(require_admin),
    service: BookingService = Depends(get_booking_service),
) -> Room:
    """Creates or updates a room. Only for facility admins."""
    room.room_id = room_id
    return service.repository.add_room(room)
