from datetime import datetime, timezone

import pytest

from roomie.errors import (
    AdvanceBookingError,
    BigRoomPolicyError,
    BookingOverlapError,
    BusinessHoursError,
    CapacityError,
    DurationError,
    SlotAlignmentError,
)
from roomie.models import Booking, BookingStatus, Room
from roomie.services import booking_rules
from tests.conftest import NOW, at

SMALL_ROOM = Room(room_id="A1-02", name="Havel", capacity=6, floor=1)
CATERING_ROOM = Room(room_id="A2-10", name="Tempelhof", capacity=16, floor=2, has_catering=True)


def make_booking(start, end, room_id="A1-02", status=BookingStatus.CONFIRMED) -> Booking:
    return Booking(
        booking_id="bk_test", room_id=room_id, owner_id="alice", title="t",
        start=start, end=end, attendees=2, status=status, created_at=NOW,
    )


def test_slot_alignment_rejects_odd_minutes():
    with pytest.raises(SlotAlignmentError):
        booking_rules.check_slot_alignment(at(10, 5), at(11))


def test_duration_limits():
    with pytest.raises(DurationError):
        booking_rules.check_duration(at(10), at(10))
    with pytest.raises(DurationError):
        booking_rules.check_duration(at(8), at(12, 15))
    booking_rules.check_duration(at(8), at(12))  # exactly 4 hours is fine


def test_business_hours_use_office_timezone():
    # 06:30 UTC is 07:30 in Berlin (CET) -> allowed
    booking_rules.check_business_hours(
        datetime(2026, 3, 3, 6, 30, tzinfo=timezone.utc), datetime(2026, 3, 3, 7, 30, tzinfo=timezone.utc)
    )
    with pytest.raises(BusinessHoursError):
        booking_rules.check_business_hours(at(19, 30), at(20, 15))


def test_weekend_is_rejected():
    saturday = 5
    with pytest.raises(BusinessHoursError):
        booking_rules.check_business_hours(at(10, days=saturday), at(11, days=saturday))


def test_advance_window():
    with pytest.raises(AdvanceBookingError):
        booking_rules.check_advance_window(at(8), NOW)
    with pytest.raises(AdvanceBookingError):
        booking_rules.check_advance_window(at(10, days=61), NOW)


def test_capacity_and_big_room_policy():
    with pytest.raises(CapacityError):
        booking_rules.check_capacity(SMALL_ROOM, 7)
    with pytest.raises(BigRoomPolicyError):
        booking_rules.check_capacity(CATERING_ROOM, 3)
    booking_rules.check_capacity(CATERING_ROOM, 4)


def test_overlap_ignores_cancelled_bookings():
    cancelled = make_booking(at(10), at(11), status=BookingStatus.CANCELLED)
    booking_rules.check_overlap(SMALL_ROOM, at(10), at(11), [cancelled])


def test_back_to_back_bookings_are_allowed_without_catering():
    existing = make_booking(at(10), at(11))
    booking_rules.check_overlap(SMALL_ROOM, at(11), at(12), [existing])


def test_catering_room_needs_cleaning_buffer():
    existing = make_booking(at(10), at(11), room_id="A2-10")
    with pytest.raises(BookingOverlapError):
        booking_rules.check_overlap(CATERING_ROOM, at(11), at(12), [existing])
    booking_rules.check_overlap(CATERING_ROOM, at(11, 15), at(12), [existing])
