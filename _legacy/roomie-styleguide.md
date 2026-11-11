# Style guide

These rules apply to all code in this repository. Reviewers refer to them by
their id, e.g. "see S-03".

## Code

- **S-01 – Formatting.** Code is formatted with `ruff format`, line length 120.
  Imports are sorted with `ruff check --select I`.
- **S-02 – Type hints.** All public functions have type hints, including the
  return type. Use `X | None` instead of `Optional[X]`.
- **S-03 – No magic numbers.** Business rules (durations, limits, hours) live
  in `roomie/config.py` and are imported from there. Do not copy their values
  into other modules or into error messages – format them from the config.
- **S-04 – Errors.** Services raise subclasses of `RoomieError`. Never raise
  `HTTPException` outside of routers, and prefer `RoomieError` in routers too.
- **S-05 – Time.** Never call `datetime.now()` or `datetime.utcnow()` directly.
  Use the injected clock (`self.clock()`) so tests can control time. All
  datetimes must be timezone-aware.
- **S-06 – Ids.** Generated ids have a type prefix: `bk_` for bookings. Rooms
  use their human readable id (e.g. `A1-02`).
- **S-07 – Docstrings.** Public functions have a docstring in numpy style if
  they have more than one parameter. Mention the ADR if the code implements a
  decision from an ADR.
- **S-08 – Logging.** Use module level loggers named `roomie.<module>`. Never
  log API keys or the full request headers.

## Tests

- **T-01 – Naming.** Test functions start with `test_` and describe the
  behaviour, e.g. `test_late_cancellation_only_for_admins`.
- **T-02 – Frozen time.** Use the `clock` fixture and the `at()` helper from
  `tests/conftest.py`. Advance time with `clock.advance(...)`.
- **T-03 – Error codes.** API tests for error cases assert the `ROOM-` code,
  not only the HTTP status.
- **T-04 – No network.** Tests must not call external services. Use the
  in-memory `Repository` and `Notifier`.

## Git

- **G-01 – Branches.** `feature/<ticket>-short-name`, `fix/<ticket>-short-name`.
  Tickets live in the Jira project `WORK`.
- **G-02 – Commits.** Conventional commits, e.g. `feat(bookings): add check-in`.
- **G-03 – Reviews.** Every merge request needs one approval from Team
  Workplace. Changes to `config.py` additionally need an approval from the
  facility management product owner.
