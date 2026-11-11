# ADR-0002: Authentication with API keys in a custom header

- Status: accepted
- Date: 2024-03-04

## Context

Roomie is called by the web app, the Slack bot and the door displays. The
company SSO (OIDC) is not available on the door displays. In addition, the
corporate reverse proxy strips the `Authorization` header for services in
the internal network zone.

## Decision

Every client gets a personal API key with the prefix `rk_live_`. The key is
sent in the custom header `X-Roomie-Key`. The header name is configured as
`API_KEY_HEADER` in `roomie/config.py`. A key maps to a user id and a role
(`employee` or `facility_admin`).

The web app exchanges the SSO session for a short-lived user key at login.

## Consequences

- `Authorization: Bearer ...` does **not** work and returns `ROOM-401-AUTH`.
- Keys must never be logged (company security requirement SEC-04).
- Key rotation is done in the secret store, see the runbook.
