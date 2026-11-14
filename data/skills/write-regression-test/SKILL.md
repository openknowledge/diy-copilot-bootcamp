---
name: write-regression-test
description: Writes a pytest regression test that reproduces a reported bug in Roomie before it is fixed (test-first bug fixing). Use it when the developer wants to fix a bug or asks for a test that reproduces a ticket.
---

# Write a regression test for a bug

Every bug fix starts with a test that reproduces the bug (TEST-07). The test must **fail
before the fix** and pass after it.

## Steps

1. **Understand the expected behaviour.** Read the ticket and find the rule that defines the
   correct behaviour (API guideline, ADR, error code table). The test asserts the *correct*
   behaviour, not the current one.
2. **Choose the level.**
   - Business rule in `roomie/services/booking_rules.py` → unit test in `tests/test_booking_rules.py`.
   - Wrong HTTP status or error body → API test in `tests/test_bookings_api.py` or `tests/test_rooms_api.py`.
3. **Name** – plain English description of the expected behaviour (TEST-02), e.g.
   `test_booking_without_timezone_is_rejected`. No ticket ids in test names.
4. **Docstring** – the first line is exactly `Regression test for <ticket id>.`, followed by one
   sentence describing the bug. This is how we find regression tests for a ticket.
5. **Arrange** – use the fixtures from `tests/conftest.py`:
   - `client` (FastAPI `TestClient` with fakes), `clock` (`FakeClock`, frozen on Monday,
     2 March 2026, 09:00 Berlin time), `notifier`
   - `booking_payload(...)` and `at(hour, minute, days)` to build requests
   - API keys `ALICE`, `BOB` (employees) and `FIONA` (facility admin)
   - Never use the real time (TEST-03) or the network (TEST-05).
6. **Assert** – for API errors assert the status **and** the error code from the body (TEST-04):
   ```python
   assert response.status_code == 422
   assert response.json()["error"]["code"] == "ROOM-422-..."
   ```
7. **Show that it fails** – tell the developer how to run only this test
   (`uv run pytest tests/<file>.py -k <test name>`) and what failure to expect before the fix.

Return the test code in a code block, followed by the command and the expected failure.
