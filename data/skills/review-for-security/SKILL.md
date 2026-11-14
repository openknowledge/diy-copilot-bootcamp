---
name: review-for-security
description: Reviews code changes or files for violations of the company's security and data protection rules (secrets, logging, personal data, access control). Use it when the developer asks for a security or privacy review, or before code that handles personal data is merged.
---

# Security and privacy review

Check the code against the binding rules of Information Security (SEC-xx) and the
Data Protection Officer (DP-xx). Violations of SEC rules are security incidents, so be precise.

## What to check

| Area | Rules | Look for |
|---|---|---|
| Secrets | SEC-01, SEC-06 | API keys, passwords or tokens in code, tests, config or comments. Demo keys (`rk_live_` in local config) are allowed only if they can't work in a deployed environment. |
| Logging | SEC-04, SEC-05 | Logged headers, request bodies, keys, names, email addresses, **meeting titles**. Logger names `roomie.<module>`, no `print()` (PY-10). |
| Personal data | DP-01, DP-02 | New fields with personal data – are they really needed? Attendee names are not needed. |
| Access | DP-05, API-06 | Can a user learn that a booking of another user exists? It must be 404, not 403. |
| Authentication | API-04 | `X-Roomie-Key` header, health endpoint without auth, admin-only endpoints use `require_admin`. |
| External services | DP-06 | Personal data sent to external services or AI tools without a data processing agreement. |

## Severity

- **BLOCKER** – must be fixed before merge: secrets in code, personal data in logs or to external services, missing access checks.
- **MAJOR** – must be fixed in this merge request or tracked in a ticket: missing tests for access rules, overly broad logging.
- **MINOR** – improvement: logger naming, comments.

## Output format

Answer with one table, ordered by severity, and nothing else before it:

| Severity | Rule | Location | Finding | Suggested fix |
|---|---|---|---|---|

- `Location` is `file:line`.
- One row per finding. If there are no findings, write one row with severity `OK`.
- After the table: one sentence saying whether the security champion has to approve (GIT-04).
