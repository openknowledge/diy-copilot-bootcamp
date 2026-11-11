"""Central configuration of the Roomie service.

All business rules that product management may want to tweak live here.
Do not hard-code these values anywhere else - import them from this module
(see the company Python coding guidelines, rule PY-03).
"""

from datetime import time
from zoneinfo import ZoneInfo

# --- General -----------------------------------------------------------------

SERVICE_NAME = "roomie"
API_VERSION = "v2"
API_PREFIX = f"/api/{API_VERSION}"

# All business-hour checks are done in the office timezone, even though
# bookings are stored in UTC (see ADR-0004).
OFFICE_TIMEZONE = ZoneInfo("Europe/Berlin")

# --- Booking rules -----------------------------------------------------------

# Bookings must start and end on a quarter-hour boundary (ADR-0001).
SLOT_MINUTES = 15

# Minimum and maximum duration of a single booking.
MIN_BOOKING_MINUTES = 15
MAX_BOOKING_MINUTES = 240

# Rooms can only be booked on weekdays within the business hours.
BUSINESS_DAYS = {0, 1, 2, 3, 4}  # Monday=0 ... Friday=4
BUSINESS_HOURS_START = time(7, 0)
BUSINESS_HOURS_END = time(20, 0)

# How far in advance a room can be booked.
MAX_ADVANCE_DAYS = 60

# Rooms with catering need time for cleaning after each booking. The buffer is
# added to the end of a booking when checking for overlaps.
CATERING_CLEANING_BUFFER_MINUTES = 15

# "Big room policy": rooms with a capacity of at least BIG_ROOM_CAPACITY may
# only be booked for at least BIG_ROOM_MIN_ATTENDEES attendees, so that small
# meetings do not block the large rooms.
BIG_ROOM_CAPACITY = 12
BIG_ROOM_MIN_ATTENDEES = 4

# --- Cancellation and check-in -----------------------------------------------

# Employees can cancel their own bookings until this many hours before the
# start. Later cancellations are only allowed for facility admins.
CANCELLATION_DEADLINE_HOURS = 2

# A booking must be checked in within this many minutes after its start,
# otherwise it is released automatically (no-show policy, ADR-0003).
CHECK_IN_GRACE_MINUTES = 10

# --- Authentication ----------------------------------------------------------

# Name of the HTTP header that carries the API key (ADR-0002).
API_KEY_HEADER = "X-Roomie-Key"

# Demo API keys. In production these are loaded from the secret store.
API_KEYS = {
    "rk_live_alice_8f3a": {"user_id": "alice", "role": "employee"},
    "rk_live_bob_2c91": {"user_id": "bob", "role": "employee"},
    "rk_live_fiona_77de": {"user_id": "fiona", "role": "facility_admin"},
}

# --- Notifications -----------------------------------------------------------

NOTIFICATION_SENDER = "roomie-noreply@example.com"
# Facility team channel which receives alerts about released (no-show) rooms.
FACILITY_ALERT_CHANNEL = "#facility-roomie"
