"""Notifications sent by Roomie.

Emails go to the booking owner, alerts about released rooms go to the
facility team channel. The default ``Notifier`` only logs the messages;
the production deployment injects ``SmtpNotifier`` (not part of this repo).
"""

import logging

from roomie.config import FACILITY_ALERT_CHANNEL, NOTIFICATION_SENDER
from roomie.models import Booking

logger = logging.getLogger("roomie.notifications")


class Notifier:
    def __init__(self) -> None:
        self.sent: list[str] = []  # kept for tests

    def _send(self, recipient: str, subject: str) -> None:
        message = f"[{NOTIFICATION_SENDER} -> {recipient}] {subject}"
        self.sent.append(message)
        logger.info(message)

    def booking_confirmed(self, booking: Booking) -> None:
        self._send(booking.owner_id, f"Booking confirmed: {booking.title} in {booking.room_id}")

    def booking_cancelled(self, booking: Booking) -> None:
        self._send(booking.owner_id, f"Booking cancelled: {booking.title} in {booking.room_id}")

    def rooms_released(self, bookings: list[Booking]) -> None:
        rooms = ", ".join(sorted({b.room_id for b in bookings}))
        self._send(FACILITY_ALERT_CHANNEL, f"Released after no-show: {rooms}")
        for booking in bookings:
            self._send(booking.owner_id, f"Your booking {booking.title} was released (no check-in).")
