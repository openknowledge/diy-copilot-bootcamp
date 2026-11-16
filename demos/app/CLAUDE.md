# Roomie – notes for coding assistants

Roomie is the meeting room booking service of Team Workplace (FastAPI, Python 3.12+).
See `README.md` for the overview and `docs/` for architecture, API, error codes and ADRs.

## Commands

```bash
uv sync                                                # install dependencies
uv run pytest -q                                       # run all tests
ROOMIE_DEMO_DATA=1 uv run uvicorn roomie.main:app --reload   # run locally (UI on :8000)
```

## Conventions

- Follow the layer rules in `docs/architecture.md`: routers → services → repository.
  Services raise `RoomieError` subclasses, never `HTTPException`.
- All business rules and settings live in `roomie/config.py` – never hard-code them.
- Error codes are stable (`docs/error_codes.md`): add new codes, never change existing ones.
- Tests use the frozen clock from `tests/conftest.py`. Never use `datetime.now()` in tests.
  Do not delete or weaken existing tests; add new tests for every bug fix.

## Company rules

Our company has binding rules for engineering, security and data protection
(rule ids like `API-07`, `PY-03`, `TEST-07`, `SEC-04`, `DP-01`). They are not in this
repository. If the tool `search_knowledge_base` is available, look up the relevant
rules before you change code, and mention the rule ids in your summary.
