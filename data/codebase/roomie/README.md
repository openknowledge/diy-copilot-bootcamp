# Roomie

Roomie is our internal service for booking meeting rooms in the Berlin office.
It is used by the Roomie web app, the Slack bot `/room` and the displays next
to every meeting room door.

Owner: Team Workplace (`#team-workplace`), on-call via the "Roomie" PagerDuty
schedule.

## Features

- List rooms and search for free rooms for a time range
- Book, cancel and check in to bookings
- Automatic release of bookings when nobody checks in (no-show policy)
- Facility admins can manage rooms and cancel any booking

## Quickstart

```bash
uv sync
uv run uvicorn roomie.main:app --reload
```

The API is then available at `http://localhost:8000/api/v2`, the interactive
docs at `http://localhost:8000/docs`.

Every request (except `/health`) needs an API key in the `X-Roomie-Key`
header. For local development use one of the demo keys from
`roomie/config.py`, e.g.:

```bash
curl -H "X-Roomie-Key: rk_live_alice_8f3a" http://localhost:8000/api/v2/rooms
```

## Running the tests

```bash
uv run pytest
```

All tests use a frozen clock (Monday, 2 March 2026, 09:00 Berlin time), see
`tests/conftest.py`. Never use `datetime.now()` in tests.

## Project layout

| Path | Content |
|---|---|
| `roomie/main.py` | App factory `create_app()` |
| `roomie/config.py` | All business rules and settings |
| `roomie/models.py` | Pydantic models |
| `roomie/errors.py` | Domain errors and error codes |
| `roomie/auth.py` | API key authentication |
| `roomie/repository.py` | In-memory storage, seed data |
| `roomie/services/` | Use cases and booking rules |
| `roomie/routers/` | HTTP endpoints |
| `roomie/scheduler.py` | Background job for no-shows |
| `docs/` | Architecture, API, error codes, ADRs, runbook |

## Further reading

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Error codes](docs/error_codes.md)
- Company-wide coding, API, testing and security guidelines: see the engineering wiki
- [Runbook](docs/runbook.md)
- [Architecture decision records](docs/adr/)
