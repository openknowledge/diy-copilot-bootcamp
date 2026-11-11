# API Design Guidelines (Version 3.2)

> **SUPERSEDED** – This version is no longer valid. It was replaced by
> version 4.0 in September 2025. The current version is
> [API Design Guidelines](../api-design-guidelines.md). Existing APIs must be
> migrated by the end of 2026.

- Owner: Architecture Board
- Version: 3.2

## Versioning

APIs are versioned with the header `Accept-Version: 1`. Version numbers in
the path are not allowed.

## Authentication

Clients authenticate with an OAuth2 access token in the standard header
`Authorization: Bearer <token>`. Technical clients use the client
credentials flow of the central identity provider.

## Error responses

Errors follow RFC 7807 ("Problem Details"):

```json
{"type": "https://errors.example.com/booking-overlap", "title": "Booking overlap", "status": 409, "detail": "Room A1-02 is already booked."}
```

The `type` URL identifies the error.

## Deleting resources

Resources are deleted with `DELETE /<collection>/{id}`. Deleted resources
return `404` afterwards.

## Status codes

Validation errors and business rule violations return `400 Bad Request`.

## Date and time

Timestamps are ISO 8601 strings. If no offset is given, the server assumes
the local time of the office (Europe/Berlin).
