# API Design Guidelines

- Owner: Engineering Guild / Architecture Board
- Applies to: all internal HTTP APIs
- Version: 4.0

## API-01 – Versioning

Every API has a version in the path: `/api/v<major>/...`, e.g. `/api/v2/bookings`.
Breaking changes require a new major version. The previous version must be
supported for at least 6 months after the new version is released.

## API-02 – Resource naming

- Use plural nouns for collections: `/bookings`, `/rooms`.
- Use kebab-case for multi-word path segments: `/release-no-shows`, `/check-in`.
- Actions that don't map to CRUD are modelled as sub-resources with `POST`,
  e.g. `POST /bookings/{id}/cancel`.

## API-03 – Deleting resources

Resources that have to be kept for statistics, audits or legal reasons are
never deleted physically ("soft delete"). They get a status such as
`cancelled` or `archived`. Such resources do **not** offer a `DELETE`
endpoint; use an action endpoint instead (`POST /{id}/cancel`).

## API-04 – Authentication

Internal services authenticate clients with API keys. The key is sent in a
custom header named `X-<Service>-Key`, e.g. `X-Roomie-Key`.

> Why not `Authorization: Bearer`? The corporate reverse proxy in the
> internal network zone strips the `Authorization` header. Additionally, not
> all clients (e.g. door displays, IoT devices) support our SSO.

Health endpoints (`/health`) don't require authentication.

## API-05 – Error responses

All errors use the same JSON body:

```json
{"error": {"code": "ROOM-409-OVERLAP", "message": "Room A1-02 is already booked from 09:00 to 10:00."}}
```

- `code` is a stable, machine-readable code of the form
  `<SERVICE>-<HTTP status>-<REASON>`. The service prefix is defined in the
  service catalogue (e.g. `ROOM` for Roomie, `PAY` for Payroll).
- `message` is a human-readable English text. Clients show their own,
  localized texts based on the `code`.
- Error codes are part of the API contract: never rename or reuse a code.
  Add a new code instead and document it.

## API-06 – Status codes

| Situation | Status |
|---|---|
| Missing or invalid API key | 401 |
| Authenticated, but not allowed | 403 |
| Resource does not exist **or the caller must not know it exists** | 404 |
| Conflict with the current state (e.g. overlapping booking) | 409 |
| Resource existed but is gone (e.g. expired, released) | 410 |
| Request is syntactically fine but violates a business rule | 422 |

Never answer a business rule violation with 500. A 500 is always a bug.

## API-07 – Date and time

- Timestamps are ISO 8601 strings **with timezone offset**, e.g.
  `2026-03-03T10:00:00+01:00` or `2026-03-03T09:00:00Z`.
- APIs reject timestamps without offset with a 422.
- Timestamps are stored in UTC. Responses return UTC (`Z`).

## API-08 – Pagination

Collections that can grow beyond 100 items are paginated with `limit`
(default 50, max 200) and an opaque `cursor`.
