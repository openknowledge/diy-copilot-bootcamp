"""Use cases around bookings: create, cancel, check in, release no-shows."""

from datetime import datetime, timedelta, timezone

from roomie import config
from roomie.errors import (
    BookingNotFoundError,
    BookingReleasedError,
    LateCancellationError,
    PermissionDeniedError,
    RoomNotFoundError,
)
from roomie.models import Booking, BookingCreate, BookingStatus, User
from roomie.notifications import Notifier
from roomie.repository import Repository
from roomie.services.booking_rules import validate_new_booking


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BookingService:
    def __init__(self, repository: Repository, notifier: Notifier, clock=utc_now) -> None:
        self.repository = repository
        self.notifier = notifier
        # The clock is injectable so that tests can control "now".
        self.clock = clock

    def create_booking(self, request: BookingCreate, user: User) -> Booking:
        room = self.repository.get_room(request.room_id)
        if room is None:
            raise RoomNotFoundError(f"Room {request.room_id} does not exist.")

        existing = self.repository.list_bookings_for_room(room.room_id)
        now = self.clock()
        validate_new_booking(request, room, existing, now)

        booking = Booking(
            booking_id=self.repository.new_booking_id(),
            room_id=room.room_id,
            owner_id=user.user_id,
            title=request.title,
            # Bookings are always stored in UTC (ADR-0004).
            start=request.start.astimezone(timezone.utc),
            end=request.end.astimezone(timezone.utc),
            attendees=request.attendees,
            created_at=now,
        )
        self.repository.add_booking(booking)
        self.notifier.booking_confirmed(booking)
        return booking

    def get_booking(self, booking_id: str, user: User) -> Booking:
        booking = self.repository.get_booking(booking_id)
        if booking is None:
            raise BookingNotFoundError(f"Booking {booking_id} does not exist.")
        if booking.owner_id != user.user_id and not user.is_admin:
            # Do not reveal that the booking exists.
            raise BookingNotFoundError(f"Booking {booking_id} does not exist.")
        return booking

    def cancel_booking(self, booking_id: str, user: User) -> Booking:
        """Cancels a booking (soft delete, see ADR-0005).

        Owners can cancel until CANCELLATION_DEADLINE_HOURS before the start.
        Facility admins can cancel any booking at any time.
        """
        booking = self.get_booking(booking_id, user)
        if not booking.is_active:
            return booking  # cancelling twice is a no-op

        now = self.clock()
        deadline = booking.start - timedelta(hours=config.CANCELLATION_DEADLINE_HOURS)
        if now > deadline and not user.is_admin:
            raise LateCancellationError(
                f"Bookings can only be cancelled up to {config.CANCELLATION_DEADLINE_HOURS} hours "
                "before the start. Please contact the facility team."
            )

        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = now
        self.repository.save_booking(booking)
        self.notifier.booking_cancelled(booking)
        return booking

    def check_in(self, booking_id: str, user: User) -> Booking:
        """Checks in a booking. Only possible from 5 minutes before the start
        until CHECK_IN_GRACE_MINUTES after the start."""
        booking = self.get_booking(booking_id, user)
        if booking.owner_id != user.user_id:
            raise PermissionDeniedError("Only the owner can check in a booking.")
        if booking.status == BookingStatus.RELEASED:
            raise BookingReleasedError("The booking was released because nobody checked in.")

        now = self.clock()
        opens_at = booking.start - timedelta(minutes=5)
        closes_at = booking.start + timedelta(minutes=config.CHECK_IN_GRACE_MINUTES)
        if not opens_at <= now <= closes_at:
            raise PermissionDeniedError("Check-in is only possible around the start of the booking.")

        booking.status = BookingStatus.CHECKED_IN
        booking.checked_in_at = now
        return self.repository.save_booking(booking)

    def release_no_shows(self) -> list[Booking]:
        """Releases all confirmed bookings whose check-in window has passed.

        Called every minute by the scheduler (see roomie/scheduler.py).
        """
        now = self.clock()
        grace = timedelta(minutes=config.CHECK_IN_GRACE_MINUTES)
        released = []
        for booking in self.repository.list_bookings_between(now - timedelta(days=1), now):
            if booking.status == BookingStatus.CONFIRMED and now > booking.start + grace:
                booking.status = BookingStatus.RELEASED
                self.repository.save_booking(booking)
                released.append(booking)
        if released:
            self.notifier.rooms_released(released)
        return released
