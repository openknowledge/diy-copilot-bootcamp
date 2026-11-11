# ADR-0004: Store in UTC, validate in the office timezone

- Status: accepted
- Date: 2024-09-02

## Context

In the first version business hours were checked in UTC. After the switch to
daylight saving time, bookings between 07:00 and 08:00 local time were
rejected for months until somebody noticed.

## Decision

- All datetimes in the API are timezone-aware ISO 8601 strings.
- Bookings are converted to UTC before they are stored.
- All checks that depend on the local day – business days, business hours
  (07:00–20:00), "same day" – and the availability view use
  `OFFICE_TIMEZONE = Europe/Berlin` from `roomie/config.py`.

## Consequences

- Responses contain UTC timestamps; clients convert them for display.
- If we open an office in another timezone, the timezone has to become a
  property of the room instead of a global setting.
