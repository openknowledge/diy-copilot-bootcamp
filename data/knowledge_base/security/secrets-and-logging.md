# Secrets and Logging Requirements

- Owner: Information Security
- Applies to: all applications and scripts
- Version: 3.0
- Binding: yes – violations are security incidents

## SEC-01 – No secrets in code

Passwords, API keys, tokens and certificates must never be committed to a
repository – not even in tests or example files. Exception: clearly marked
**demo keys** that only work against a local development setup, e.g. keys
with the prefix `rk_live_` in local config files. Such demo keys must never be
accepted by a deployed environment.

Production secrets are stored in the central secret store and injected into
the application as environment variables or files at runtime.

## SEC-02 – Secret scanning

All repositories are scanned for secrets on every push. If a secret was
committed, it is considered **compromised**: rotate it immediately (removing
the commit is not enough) and inform `#security` in Slack.

## SEC-03 – Key rotation

API keys of technical clients (bots, displays, other services) are rotated at
least every **90 days**. Keys of former employees are revoked on their last
working day.

## SEC-04 – What must never be logged

- API keys, tokens, passwords, session ids
- Complete request or response headers
- Request bodies of endpoints that handle personal data
- Personal data beyond the user id (no names, email addresses or meeting
  titles in logs)

If you need to correlate requests, log the user id and a request id.

## SEC-05 – Logging conventions

- Use the standard `logging` module with module-level loggers named
  `<service>.<module>`, e.g. `roomie.notifications`.
- Log levels: `ERROR` for failures that need attention, `WARNING` for
  unexpected but handled situations, `INFO` for important business events,
  `DEBUG` for details (disabled in production).
- Logs are kept for **30 days** in the central log platform.

## SEC-06 – Sharing secrets

Never share secrets via Slack, email, tickets or AI assistants. Use the
secret store's sharing function, which creates a one-time link.
