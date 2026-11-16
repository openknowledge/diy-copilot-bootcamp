"""Shared fixtures.

All tests run against a frozen clock: Monday, 2 March 2026, 09:00 in Berlin.
Use the ``at`` helper to build timezone-aware datetimes relative to that day.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from roomie.config import OFFICE_TIMEZONE
from roomie.main import create_app
from roomie.notifications import Notifier
from roomie.repository import Repository

NOW = datetime(2026, 3, 2, 9, 0, tzinfo=OFFICE_TIMEZONE)

ALICE = {"X-Roomie-Key": "rk_live_alice_8f3a"}
BOB = {"X-Roomie-Key": "rk_live_bob_2c91"}
FIONA = {"X-Roomie-Key": "rk_live_fiona_77de"}  # facility admin


def at(hour: int, minute: int = 0, days: int = 0) -> datetime:
    """Returns a Berlin datetime on the test day (+ days) at hour:minute."""
    return (NOW + timedelta(days=days)).replace(hour=hour, minute=minute)


class FakeClock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(NOW)


@pytest.fixture
def notifier() -> Notifier:
    return Notifier()


@pytest.fixture
def client(clock, notifier) -> TestClient:
    app = create_app(repository=Repository(), notifier=notifier, clock=clock)
    return TestClient(app)


def booking_payload(room_id="A1-02", start=None, end=None, attendees=2, title="Weekly sync") -> dict:
    start = start or at(14, days=1)
    end = end or at(15, days=1)
    return {
        "room_id": room_id,
        "title": title,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "attendees": attendees,
    }
