# ADR-0003: Automatic release of no-show bookings

- Status: accepted
- Date: 2024-06-20

## Context

An analysis of the door sensors showed that about 30% of all booked meetings
never took place. The rooms were blocked while people searched for a free
room.

## Decision

A booking must be checked in by its owner. Check-in is possible from
5 minutes before the start until 10 minutes after the start
(`CHECK_IN_GRACE_MINUTES = 10`). If nobody checks in, the booking is set to
the status `released` and the room becomes free again.

The release job runs every 60 seconds inside one API replica
(`roomie/scheduler.py`). Released bookings are reported to the facility team
channel `#facility-roomie`, and the owner gets an email.

A released booking cannot be checked in anymore (`ROOM-410-RELEASED`); the
user has to create a new booking.

## Consequences

- Door displays and the Slack bot need a check-in button.
- Bookings by facility admins are not exempt – admins must check in, too.
