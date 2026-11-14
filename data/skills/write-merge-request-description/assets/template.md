## <ticket id>: <summary>

### Why
<!-- The problem from the user's perspective, link to the ticket, guideline or ADR -->

### What changed
<!-- Bullet list per layer: routers, services, config, errors, tests, docs -->

### How it was tested
<!-- Regression test (name of the test) and manual reproduction -->

### Required approvals
- [ ] Team Workplace member
- [ ] Product owner facility management (only if `config.py` / business rules changed)
- [ ] Security champion (only if authentication, authorization or personal data changed)

### Checklist
- [ ] CI pipeline is green (formatting, linting, tests, coverage, security scan)
- [ ] New error codes are documented in `docs/error_codes.md` and announced in `#team-workplace`
- [ ] Contains AI-generated code (reviewed like human-written code, GIT-05)
