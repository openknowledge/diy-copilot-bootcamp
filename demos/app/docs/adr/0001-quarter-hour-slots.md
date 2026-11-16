# ADR-0001: Bookings use 15-minute slots

- Status: accepted
- Date: 2024-02-12

## Context

Before Roomie, rooms were booked via shared calendars. People booked
arbitrary times like 10:07–10:52, which left small unusable gaps between
meetings and made the door displays hard to read.

## Decision

Bookings must start and end on a 15-minute boundary (`:00`, `:15`, `:30`,
`:45`). The slot length is configured as `SLOT_MINUTES` in
`roomie/config.py`. Violations are rejected with `ROOM-422-SLOT`; the API does
not round automatically, because silent rounding confused users in the pilot.

The minimum duration equals one slot (15 minutes), the maximum duration is
4 hours (`MAX_BOOKING_MINUTES = 240`) so that rooms cannot be blocked for a
whole day. Workshops that need a room longer must be booked by the facility
team as multiple bookings.

## Consequences

- Clients must offer only quarter-hour times in their pickers.
- The availability view can be rendered as a simple grid.
