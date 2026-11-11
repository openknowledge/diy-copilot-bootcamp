# Git Workflow and Code Review

- Owner: Engineering Guild
- Version: 2.0

## GIT-01 – Branches

- `main` is always deployable. Direct pushes to `main` are blocked.
- Feature branches: `feature/<ticket>-short-name`, e.g. `feature/WORK-415-recurring-bookings`.
- Bug fix branches: `fix/<ticket>-short-name`, e.g. `fix/WORK-412-naive-datetimes`.
- Tickets live in Jira. Each team has its own project key (e.g. `WORK` for
  Team Workplace).

## GIT-02 – Commit messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.
Example: `fix(bookings): reject timestamps without timezone offset`.
Mention the ticket in the commit body (`Refs: WORK-412`).

## GIT-03 – Merge requests

- A merge request should be small: aim for less than 400 changed lines.
- The description explains *why* the change is needed and how it was tested.
- The CI pipeline (formatting, linting, tests, coverage, security scan) must
  be green before review.

## GIT-04 – Reviews and approvals

- Every merge request needs **one approval** from a member of the owning team.
- Changes to **business rules** (e.g. values in `config.py` such as booking
  durations, deadlines or limits) additionally need an approval from the
  **product owner** of the business department (e.g. facility management for
  Roomie).
- Changes to authentication, authorization or handling of personal data
  additionally need an approval from the **security champion** of the team.

## GIT-05 – AI-generated code

Code generated with AI assistants is reviewed exactly like human-written
code. The author is responsible for it. See the
[AI assistant usage policy](../security/ai-assistant-usage-policy.md).

## GIT-06 – Releases

Releases are tagged with semantic versions (`v2.3.1`). The changelog is
generated from the commit messages.
