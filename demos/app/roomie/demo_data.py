"""Demo bookings, so that the UI does not start empty.

Only used when ``ROOMIE_DEMO_DATA=1`` is set (the Docker image does this).
The tests always start with an empty repository.
"""

import os
from datetime import date, datetime, time, timedelta, timezone

from roomie import config
from roomie.models import Booking
from roomie.repository import Repository

# (days after the next business day, room, owner, title, start, end, attendees)
_DEMO_BOOKINGS = [
    (0, "A1-02", "alice", "Sprint planning", time(10, 0), time(11, 30), 5),
    (0, "A2-10", "fiona", "All hands Workplace", time(14, 0), time(16, 0), 14),
    (0, "B2-14", "bob", "Architecture review", time(9, 0), time(10, 0), 6),
    (1, "A1-01", "bob", "1:1", time(13, 0), time(13, 30), 2),
    (1, "A1-02", "alice", "Backlog refinement", time(15, 0), time(16, 0), 4),
    (2, "A2-10", "fiona", "Customer workshop", time(9, 0), time(13, 0), 10),
    (2, "B3-01", "alice", "Focus time", time(8, 0), time(10, 0), 1),
    (3, "A1-02", "bob", "Retro", time(16, 0), time(17, 0), 6),
]


def demo_data_enabled() -> bool:
    return os.getenv("ROOMIE_DEMO_DATA", "0") == "1"


def _business_days_from(start: date, count: int) -> list[date]:
    days, day = [], start
    while len(days) < count:
        if day.weekday() in config.BUSINESS_DAYS:
            days.append(day)
        day += timedelta(days=1)
    return days


def seed_demo_bookings(repository: Repository, now: datetime) -> None:
    """Adds bookings on the next business days, relative to ``now``.

    The bookings are added directly to the repository (without validation),
    so that the demo also works if it is started late in the evening.
    """
    local_now = now.astimezone(config.OFFICE_TIMEZONE)
    days = _business_days_from(local_now.date() + timedelta(days=1), 4)
    for offset, room_id, owner_id, title, start, end, attendees in _DEMO_BOOKINGS:
        day = days[offset]
        repository.add_booking(
            Booking(
                booking_id=repository.new_booking_id(),
                room_id=room_id,
                owner_id=owner_id,
                title=title,
                start=datetime.combine(day, start, tzinfo=config.OFFICE_TIMEZONE).astimezone(timezone.utc),
                end=datetime.combine(day, end, tzinfo=config.OFFICE_TIMEZONE).astimezone(timezone.utc),
                attendees=attendees,
                created_at=now,
            )
        )
