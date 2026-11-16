# ADR-0005: Bookings are never deleted

- Status: accepted
- Date: 2025-01-15

## Context

Facility management wants statistics about cancellations and no-shows to plan
the number and size of rooms. Hard deletes made this impossible.

## Decision

Bookings are never deleted. Cancelling sets the status to `cancelled` and
stores `cancelled_at`. Therefore cancelling is exposed as
`POST /bookings/{id}/cancel` instead of `DELETE /bookings/{id}`.

Employees can cancel their own bookings until 2 hours before the start
(`CANCELLATION_DEADLINE_HOURS`). Later cancellations return
`ROOM-403-LATE-CANCEL`; only facility admins can cancel at any time.
Cancelling an already cancelled booking is a no-op and returns the booking.

## Consequences

- Queries for "active" bookings must filter by status
  (`ACTIVE_STATUSES = {confirmed, checked_in}` in `roomie/models.py`).
- Personal data in old bookings is anonymised after 12 months by a separate
  job in the data platform.
