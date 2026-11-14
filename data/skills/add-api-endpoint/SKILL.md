---
name: add-api-endpoint
description: Step-by-step guide for adding a new HTTP endpoint to the Roomie service (FastAPI), from the route to the error codes and tests. Use it when the developer wants to add or change an API endpoint of Roomie.
---

# Add an API endpoint to Roomie

Roomie follows the layered structure of the Python coding guidelines: routers → services →
repository, configuration in `config.py`. Work through the steps in this order.

## 1. Design the endpoint

- Path under `/api/v2/...` (API-01), plural nouns, kebab-case (API-02).
- Actions that are not CRUD are `POST` sub-resources, e.g. `POST /bookings/{id}/check-in`.
- **No `DELETE` for bookings** – they are cancelled, never deleted (API-03, ADR-0005).
- Timestamps in requests must have a timezone offset; responses return UTC (API-07, ADR-0004).
- If the collection can grow beyond 100 items: `limit`/`cursor` pagination (API-08).

## 2. Models (`roomie/models.py`)

- Request bodies are Pydantic models named `<Thing>Create` / `<Thing>Update`.
- Generated ids get a type prefix, e.g. `bk_` for bookings (PY-07).

## 3. Business logic (`roomie/services/`)

- All rules live in the service, never in the router.
- Limits and durations come from `roomie/config.py` (PY-03) – no magic numbers,
  also not in error messages.
- Use the injected clock instead of `datetime.now()` (PY-05).
- Raise domain errors from `roomie/errors.py`, never `HTTPException` (PY-06).

## 4. Errors (`roomie/errors.py`, `docs/error_codes.md`)

- Reuse an existing error if the meaning is exactly the same.
- Otherwise add a subclass of `RoomieError` with `status_code` and a new code
  `ROOM-<status>-<REASON>` (API-05, API-06). Never rename or reuse a code.
- Add the code to the table in `docs/error_codes.md` and announce it in `#team-workplace`.

## 5. Router (`roomie/routers/`)

- Authentication via `Depends(get_current_user)` or `Depends(require_admin)` (API-04).
- The service via `Depends(get_booking_service)` (PY-09).
- Bookings of other users answer 404, not 403 (DP-05).

## 6. Tests (`tests/`)

- API tests with the `client` fixture from `tests/conftest.py`, time via the `clock` fixture (TEST-03).
- One test per error case that asserts the **error code** (TEST-04).
- Use `booking_payload()` and `at()` from `conftest.py` to build requests.

## 7. Documentation

- Add the endpoint to `docs/api.md`.
- If you made an architecture decision, write an ADR (skill `write-adr`).
