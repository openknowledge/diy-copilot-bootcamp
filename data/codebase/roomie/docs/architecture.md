# Architecture

Roomie is a small layered FastAPI service.

```
HTTP request
   │
   ▼
routers/        – parse the request, check auth, call a service
   │
   ▼
services/       – use cases (BookingService, AvailabilityService)
   │              and pure validation rules (booking_rules.py)
   ▼
repository.py   – storage (in-memory locally, PostgreSQL in production)
```

## Rules for the layers

1. Routers never talk to the repository for write operations. Reading through
   `service.repository` is tolerated for simple list endpoints.
2. Services raise `RoomieError` subclasses, never `HTTPException`. The
   conversion to HTTP responses happens centrally in
   `errors.roomie_error_handler`.
3. Business rules in `booking_rules.py` are pure functions without side
   effects. They get "now" passed in instead of calling the clock themselves.
4. Services get their collaborators (repository, notifier, clock) through the
   constructor. `create_app()` wires everything together.

## Booking lifecycle

```
            create
              │
              ▼
         ┌─────────┐   check-in    ┌────────────┐
         │confirmed│──────────────▶│ checked_in │
         └─────────┘               └────────────┘
          │      │
   cancel │      │ no check-in within 10 min after start
          ▼      ▼
   ┌─────────┐ ┌──────────┐
   │cancelled│ │ released │
   └─────────┘ └──────────┘
```

Only `confirmed` and `checked_in` bookings block a room.

## Time handling

- Clients send timezone-aware ISO 8601 timestamps.
- Bookings are stored in UTC.
- Business hours, weekdays and the availability view are evaluated in the
  office timezone `Europe/Berlin`.

See ADR-0004 for the reasoning.

## Production setup

- 3 API replicas behind the internal load balancer
- PostgreSQL 16 (managed), schema migrations with Alembic (separate repo
  `roomie-migrations`)
- Exactly one replica runs the no-show scheduler (`ROOMIE_RUN_SCHEDULER=1`)
- Emails via the company SMTP relay, alerts to Slack `#facility-roomie`
