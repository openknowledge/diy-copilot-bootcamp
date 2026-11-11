# Glossary – Workplace Domain

Terms used by Facility Management and Team Workplace. Use these terms in user
interfaces, documentation and code (in English, e.g. as class or variable
names).

| Term | Meaning |
|---|---|
| **Booking** | Reservation of a meeting room by one person (the *owner*) for a time range. |
| **Owner** | The person who created a booking. Only the owner can check in. |
| **Attendees** | Number of people expected in a meeting, including the owner. |
| **Slot** | A quarter hour; bookings always cover whole slots. |
| **Business hours** | Monday to Friday, 07:00–20:00 Berlin time. |
| **Check-in** | Confirmation that a booked meeting actually takes place, from 5 minutes before until 10 minutes after the start. |
| **No-show** | A booking nobody checked in to. |
| **Release** | Automatic freeing of a room after a no-show. The booking gets the status *released*. |
| **Cancellation** | The owner (or a facility admin) withdraws a booking. The booking gets the status *cancelled* and is kept for statistics. |
| **Late cancellation** | A cancellation less than 2 hours before the start; only allowed for facility admins. |
| **Big room** | A room with 12 or more seats. Subject to the big room policy (min. 4 attendees). |
| **Cleaning buffer** | 15 minutes after each booking of a room with catering, during which the room cannot be booked. |
| **Facility admin** | Member of the facility team with extended permissions. |
| **Room id** | Identifier of a room in the form `<building><floor>-<number>`, e.g. `B2-14`. |
| **Desk** | A workplace in the open space. Desks are booked with Deskly, not with Roomie. |
