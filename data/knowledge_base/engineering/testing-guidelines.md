# Testing Guidelines

- Owner: Engineering Guild
- Applies to: all services
- Version: 1.6

## TEST-01 – Test framework

We use `pytest`. Tests live in the folder `tests/` next to the package. API
tests use FastAPI's `TestClient` against an app created by the app factory
(`create_app()`), with all external collaborators replaced by fakes.

## TEST-02 – Naming

Test functions start with `test_` and describe the expected behaviour in
plain English, e.g. `test_late_cancellation_only_for_admins`. Avoid names
like `test_cancel_2`.

## TEST-03 – Controlling time

Tests never depend on the real current time. Use a fake clock that is
injected into the code under test (see coding guideline PY-05) and advance
it explicitly, e.g. `clock.advance(minutes=30)`. A test that only fails at
certain times of the day is a bug in the test.

## TEST-04 – Error cases

Tests for error cases of an API assert the error **code** from the response
body (e.g. `ROOM-403-LATE-CANCEL`), not only the HTTP status. Several errors
share the same status, so the status alone does not prove the right rule was
triggered.

## TEST-05 – No network

Unit and API tests must not call external services (databases, mail servers,
other APIs, LLMs). Use in-memory fakes. Integration tests against real
infrastructure are marked with `@pytest.mark.integration` and run only in the
nightly pipeline.

## TEST-06 – Coverage

New code must have a line coverage of at least **80%**. Business rules
should be covered completely, including boundary values (e.g. exactly the
maximum duration).

## TEST-07 – Bug fixes

Every bug fix starts with a test that reproduces the bug. The test must fail
before the fix and pass after it. Reference the ticket in the test's
docstring.

## Definition of Done (testing part)

- All tests pass in the CI pipeline.
- Coverage of new code ≥ 80%.
- Error cases assert error codes.
- No skipped tests without a ticket reference.
