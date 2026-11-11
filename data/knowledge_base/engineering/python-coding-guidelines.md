# Python Coding Guidelines

- Owner: Engineering Guild
- Applies to: all Python services of the company
- Version: 2.1

These rules apply to all Python code. Reviewers refer to them by their id,
e.g. "see PY-03". Deviations need a comment in the code explaining why.

## Formatting and tooling

- **PY-01 – Formatting.** Code is formatted with `ruff format`, line length
  120. Imports are sorted with `ruff check --select I`. The CI pipeline fails
  if the code is not formatted.
- **PY-02 – Python version.** New services use the latest Python version
  supported by our base images (currently 3.12). Dependencies are managed
  with `uv`.

## Code

- **PY-03 – No magic numbers.** Business rules and limits (durations,
  thresholds, opening hours, ...) are defined once in a central configuration
  module (usually `config.py`) and imported from there. Do not copy their
  values into other modules, tests or error messages – format messages from
  the configuration instead.
- **PY-04 – Type hints.** All public functions have type hints, including the
  return type. Use `X | None` instead of `Optional[X]` and built-in generics
  (`list[str]`) instead of `typing.List`.
- **PY-05 – Time.** Never call `datetime.now()`, `datetime.utcnow()` or
  `date.today()` in business logic. Inject a clock (a callable returning the
  current time) so that tests can control time. All datetimes must be
  timezone-aware; naive datetimes are a bug.
- **PY-06 – Errors.** Services define their own exception hierarchy with one
  base class per service. Business logic raises these domain exceptions, never
  framework exceptions such as FastAPI's `HTTPException`. The conversion into
  HTTP responses happens in one central exception handler.
- **PY-07 – Identifiers.** Generated ids are prefixed with a short type prefix
  followed by an underscore, e.g. `bk_` for bookings or `inv_` for invoices.
  This makes ids recognisable in logs.
- **PY-08 – Docstrings.** Public functions with more than one parameter have
  a docstring in numpy style. If code implements an architecture decision,
  reference the ADR (e.g. "see ADR-0004").
- **PY-09 – Dependency injection.** Classes get their collaborators
  (repositories, clients, clocks) through the constructor. Do not create them
  inside methods and do not use global singletons for them.
- **PY-10 – Print statements.** Never use `print()` in service code. Use the
  module logger (see [Secrets and logging](../security/secrets-and-logging.md)).

## Structure of a service

Services follow a layered structure:

| Layer | Folder | Responsibility |
|---|---|---|
| HTTP | `routers/` | Parse requests, authentication, call services |
| Use cases | `services/` | Business logic, validation rules |
| Persistence | `repository.py` | Database access |
| Configuration | `config.py` | Settings and business rules |

Routers must not contain business logic.
