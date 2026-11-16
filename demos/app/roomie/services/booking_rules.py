"""Validation rules for bookings.

Each rule is a small function that raises a RoomieError if the rule is
violated. ``validate_new_booking`` runs all rules in a fixed order, so that
clients always get the most fundamental error first.
"""

from datetime import datetime, timedelta

from roomie import config
from roomie.errors import (
    AdvanceBookingError,
    BigRoomPolicyError,
    BookingOverlapError,
    BusinessHoursError,
    CapacityError,
    DurationError,
    SlotAlignmentError,
)
from roomie.models import Booking, BookingCreate, Room


def check_slot_alignment(start: datetime, end: datetime) -> None:
    """Start and end must lie on a SLOT_MINUTES boundary (ADR-0001)."""
    for moment in (start, end):
        if moment.minute % config.SLOT_MINUTES != 0 or moment.second or moment.microsecond:
            raise SlotAlignmentError(
                f"Bookings must start and end on a {config.SLOT_MINUTES}-minute boundary."
            )


def check_duration(start: datetime, end: datetime) -> None:
    """The booking must last between MIN and MAX_BOOKING_MINUTES."""
    minutes = (end - start).total_seconds() / 60
    if minutes < config.MIN_BOOKING_MINUTES:
        raise DurationError(f"A booking must last at least {config.MIN_BOOKING_MINUTES} minutes.")
    if minutes > config.MAX_BOOKING_MINUTES:
        raise DurationError(f"A booking must not last longer than {config.MAX_BOOKING_MINUTES} minutes.")


def check_business_hours(start: datetime, end: datetime) -> None:
    """Bookings must be on a business day and within business hours.

    The check is done in the office timezone, not in UTC (ADR-0004).
    """
    local_start = start.astimezone(config.OFFICE_TIMEZONE)
    local_end = end.astimezone(config.OFFICE_TIMEZONE)
    if local_start.weekday() not in config.BUSINESS_DAYS:
        raise BusinessHoursError("Rooms can only be booked from Monday to Friday.")
    if local_start.date() != local_end.date():
        raise BusinessHoursError("A booking must start and end on the same day.")
    if local_start.time() < config.BUSINESS_HOURS_START or local_end.time() > config.BUSINESS_HOURS_END:
        raise BusinessHoursError(
            f"Rooms can only be booked between {config.BUSINESS_HOURS_START:%H:%M} "
            f"and {config.BUSINESS_HOURS_END:%H:%M}."
        )


def check_advance_window(start: datetime, now: datetime) -> None:
    """Bookings must be in the future and at most MAX_ADVANCE_DAYS ahead."""
    if start <= now:
        raise AdvanceBookingError("Bookings must start in the future.")
    if start - now > timedelta(days=config.MAX_ADVANCE_DAYS):
        raise AdvanceBookingError(
            f"Rooms can be booked at most {config.MAX_ADVANCE_DAYS} days in advance."
        )


def check_capacity(room: Room, attendees: int) -> None:
    """Attendees must fit into the room and respect the big room policy."""
    if attendees > room.capacity:
        raise CapacityError(
            f"Room {room.room_id} has a capacity of {room.capacity}, but {attendees} attendees were requested."
        )
    if room.capacity >= config.BIG_ROOM_CAPACITY and attendees < config.BIG_ROOM_MIN_ATTENDEES:
        raise BigRoomPolicyError(
            f"Rooms with {config.BIG_ROOM_CAPACITY}+ seats require at least "
            f"{config.BIG_ROOM_MIN_ATTENDEES} attendees. Please choose a smaller room."
        )


def effective_end(booking_end: datetime, room: Room) -> datetime:
    """Returns the end of a booking including the cleaning buffer for catering rooms."""
    if room.has_catering:
        return booking_end + timedelta(minutes=config.CATERING_CLEANING_BUFFER_MINUTES)
    return booking_end


def check_overlap(room: Room, start: datetime, end: datetime, existing: list[Booking]) -> None:
    """The new booking must not overlap any active booking of the room.

    For catering rooms the cleaning buffer is added to the end of every
    booking, including the new one.
    """
    new_end = effective_end(end, room)
    for booking in existing:
        if not booking.is_active:
            continue
        if start < effective_end(booking.end, room) and booking.start < new_end:
            raise BookingOverlapError(
                f"Room {room.room_id} is already booked from {booking.start:%H:%M} to {booking.end:%H:%M}."
            )


def validate_new_booking(
    request: BookingCreate, room: Room, existing: list[Booking], now: datetime
) -> None:
    """Runs all booking rules in order. Raises the first violation."""
    check_slot_alignment(request.start, request.end)
    check_duration(request.start, request.end)
    check_business_hours(request.start, request.end)
    check_advance_window(request.start, now)
    check_capacity(room, request.attendees)
    check_overlap(room, request.start, request.end, existing)
