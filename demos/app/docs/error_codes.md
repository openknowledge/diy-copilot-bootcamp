# Error codes

Every domain error has a stable code `ROOM-<status>-<reason>`. Clients (web
app, Slack bot, door displays) show localized messages based on the code, so
**codes must never be renamed or reused**. Add a new code instead and announce
it in `#team-workplace`.

| Code | HTTP | Exception | When |
|---|---|---|---|
| `ROOM-401-AUTH` | 401 | `AuthenticationError` | `X-Roomie-Key` header missing or key unknown |
| `ROOM-403-FORBIDDEN` | 403 | `PermissionDeniedError` | Action needs another role, or check-in outside the check-in window |
| `ROOM-403-LATE-CANCEL` | 403 | `LateCancellationError` | Employee cancels less than 2 hours before the start |
| `ROOM-404-ROOM` | 404 | `RoomNotFoundError` | Unknown room id |
| `ROOM-404-BOOKING` | 404 | `BookingNotFoundError` | Unknown booking id, or the booking belongs to someone else |
| `ROOM-409-OVERLAP` | 409 | `BookingOverlapError` | Room already booked (incl. cleaning buffer for catering rooms) |
| `ROOM-410-RELEASED` | 410 | `BookingReleasedError` | Check-in to a booking that was released after a no-show |
| `ROOM-422-SLOT` | 422 | `SlotAlignmentError` | Start or end not on a 15-minute boundary |
| `ROOM-422-DURATION` | 422 | `DurationError` | Shorter than 15 minutes or longer than 4 hours |
| `ROOM-422-HOURS` | 422 | `BusinessHoursError` | Weekend, outside 07:00–20:00 Berlin time, or across midnight |
| `ROOM-422-ADVANCE` | 422 | `AdvanceBookingError` | Start in the past or more than 60 days ahead |
| `ROOM-422-CAPACITY` | 422 | `CapacityError` | More attendees than seats |
| `ROOM-422-BIG-ROOM` | 422 | `BigRoomPolicyError` | Room with 12+ seats booked for fewer than 4 attendees |

## Adding a new error

1. Add a subclass of `RoomieError` in `roomie/errors.py` with `status_code`
   and `code`.
2. Add a row to the table above.
3. Add a test that asserts the code in the response body.

Validation errors raised by FastAPI itself (malformed JSON, missing fields)
keep FastAPI's default 422 format and have no `ROOM-` code.
