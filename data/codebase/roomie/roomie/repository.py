"""In-memory persistence for rooms and bookings.

The repository hides the storage from the services. In production a
PostgreSQL implementation with the same interface is used; for local
development and tests this in-memory version is sufficient.
"""

import uuid
from datetime import datetime

from roomie.models import Booking, Room


class Repository:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._bookings: dict[str, Booking] = {}

    # --- Rooms -----------------------------------------------------------------

    def add_room(self, room: Room) -> Room:
        self._rooms[room.room_id] = room
        return room

    def get_room(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    def list_rooms(self) -> list[Room]:
        return sorted(self._rooms.values(), key=lambda room: room.room_id)

    # --- Bookings --------------------------------------------------------------

    def add_booking(self, booking: Booking) -> Booking:
        self._bookings[booking.booking_id] = booking
        return booking

    def get_booking(self, booking_id: str) -> Booking | None:
        return self._bookings.get(booking_id)

    def save_booking(self, booking: Booking) -> Booking:
        # Bookings are never deleted, only their status changes (ADR-0005).
        self._bookings[booking.booking_id] = booking
        return booking

    def list_bookings_for_room(self, room_id: str) -> list[Booking]:
        return sorted(
            (b for b in self._bookings.values() if b.room_id == room_id),
            key=lambda b: b.start,
        )

    def list_bookings_for_owner(self, owner_id: str) -> list[Booking]:
        return sorted(
            (b for b in self._bookings.values() if b.owner_id == owner_id),
            key=lambda b: b.start,
        )

    def list_bookings_between(self, start: datetime, end: datetime) -> list[Booking]:
        return [b for b in self._bookings.values() if b.start < end and b.end > start]

    @staticmethod
    def new_booking_id() -> str:
        # Booking ids are prefixed so they can be recognised in logs.
        return f"bk_{uuid.uuid4().hex[:12]}"


def seed_rooms(repository: Repository) -> None:
    """Adds the rooms of the Berlin office to the repository."""
    rooms = [
        Room(room_id="A1-01", name="Spree", capacity=4, floor=1, has_video=True),
        Room(room_id="A1-02", name="Havel", capacity=6, floor=1, has_video=True),
        Room(room_id="A2-10", name="Tempelhof", capacity=16, floor=2, has_video=True, has_catering=True),
        Room(room_id="B2-14", name="Wannsee", capacity=8, floor=2),
        Room(room_id="B3-01", name="Focus Box", capacity=1, floor=3),
    ]
    for room in rooms:
        repository.add_room(room)
