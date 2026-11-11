# API

Base path: `/api/v2`. All endpoints except `/health` require the
`X-Roomie-Key` header.

## Rooms

| Method | Path | Description | Role |
|---|---|---|---|
| GET | `/rooms` | List all rooms | employee |
| GET | `/rooms/search?start=&end=&attendees=&needs_video=` | Free rooms for a time range, smallest suitable room first | employee |
| GET | `/rooms/{room_id}` | Get a single room | employee |
| GET | `/rooms/{room_id}/availability?day=YYYY-MM-DD` | Free slots of a room on a day (office timezone) | employee |
| PUT | `/rooms/{room_id}` | Create or update a room | facility_admin |

Room ids follow the pattern `<building><floor>-<number>`, e.g. `B2-14` is
room 14 on floor 2 of building B.

## Bookings

| Method | Path | Description | Role |
|---|---|---|---|
| POST | `/bookings` | Create a booking | employee |
| GET | `/bookings/mine` | List own bookings | employee |
| GET | `/bookings/{booking_id}` | Get a booking (owner or admin only) | employee |
| POST | `/bookings/{booking_id}/cancel` | Cancel a booking | owner / facility_admin |
| POST | `/bookings/{booking_id}/check-in` | Check in to a booking | owner |
| POST | `/bookings/release-no-shows` | Trigger the no-show job manually | facility_admin |

### Example: create a booking

```http
POST /api/v2/bookings
X-Roomie-Key: rk_live_alice_8f3a
Content-Type: application/json

{
  "room_id": "A1-02",
  "title": "Sprint planning",
  "start": "2026-03-03T10:00:00+01:00",
  "end": "2026-03-03T11:30:00+01:00",
  "attendees": 5
}
```

Response `201 Created`:

```json
{
  "booking_id": "bk_3f9c0a1b2d4e",
  "room_id": "A1-02",
  "owner_id": "alice",
  "title": "Sprint planning",
  "start": "2026-03-03T09:00:00Z",
  "end": "2026-03-03T10:30:00Z",
  "attendees": 5,
  "status": "confirmed",
  "created_at": "2026-03-02T08:00:00Z",
  "cancelled_at": null,
  "checked_in_at": null
}
```

Note that `start` and `end` are returned in UTC.

## Errors

All errors use the same body:

```json
{"error": {"code": "ROOM-409-OVERLAP", "message": "Room A1-02 is already booked from 09:00 to 10:00."}}
```

See [error_codes.md](error_codes.md) for the full list.
