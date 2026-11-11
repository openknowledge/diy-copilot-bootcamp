"""Finds free rooms and free time slots."""

from datetime import date, datetime, timedelta

from roomie import config
from roomie.errors import RoomNotFoundError
from roomie.models import Room
from roomie.repository import Repository
from roomie.services.booking_rules import effective_end


class AvailabilityService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def free_slots(self, room_id: str, day: date) -> list[tuple[datetime, datetime]]:
        """Returns the free time ranges of a room on a given (local) day.

        The ranges are given in the office timezone and respect the cleaning
        buffer of catering rooms.
        """
        room = self.repository.get_room(room_id)
        if room is None:
            raise RoomNotFoundError(f"Room {room_id} does not exist.")

        day_start = datetime.combine(day, config.BUSINESS_HOURS_START, tzinfo=config.OFFICE_TIMEZONE)
        day_end = datetime.combine(day, config.BUSINESS_HOURS_END, tzinfo=config.OFFICE_TIMEZONE)

        busy = [
            (b.start, effective_end(b.end, room))
            for b in self.repository.list_bookings_for_room(room_id)
            if b.is_active and b.start < day_end and b.end > day_start
        ]

        free = []
        cursor = day_start
        for busy_start, busy_end in sorted(busy):
            if busy_start > cursor:
                free.append((cursor, busy_start.astimezone(config.OFFICE_TIMEZONE)))
            cursor = max(cursor, busy_end.astimezone(config.OFFICE_TIMEZONE))
        if cursor < day_end:
            free.append((cursor, day_end))
        return free

    def find_rooms(self, start: datetime, end: datetime, attendees: int, needs_video: bool = False) -> list[Room]:
        """Returns all rooms that are free in the given range and suitable for
        the number of attendees, smallest room first."""
        candidates = []
        for room in self.repository.list_rooms():
            if room.capacity < attendees:
                continue
            if room.capacity >= config.BIG_ROOM_CAPACITY and attendees < config.BIG_ROOM_MIN_ATTENDEES:
                continue
            if needs_video and not room.has_video:
                continue
            if self._is_free(room, start, end):
                candidates.append(room)
        return sorted(candidates, key=lambda room: room.capacity)

    def _is_free(self, room: Room, start: datetime, end: datetime) -> bool:
        new_end = end + timedelta(minutes=config.CATERING_CLEANING_BUFFER_MINUTES) if room.has_catering else end
        for booking in self.repository.list_bookings_for_room(room.room_id):
            if booking.is_active and start < effective_end(booking.end, room) and booking.start < new_end:
                return False
        return True
