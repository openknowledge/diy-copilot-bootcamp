---
name: write-adr
description: Drafts an Architecture Decision Record (ADR) for the Roomie service in the team's format. Use it when the developer made or wants to document an architecture or design decision.
---

# Write an Architecture Decision Record

Roomie documents decisions in `docs/adr/` (see the existing ADRs 0001–0005). Code that
implements a decision refers to it in its docstring (PY-08), e.g. "see ADR-0004".

## Steps

1. **Number** – the next free four-digit number after the existing ADRs
   (currently the next one is `0006`). File name: `docs/adr/<number>-<short-kebab-title>.md`.
2. **Template** – use `assets/template.md` of this skill. Keep the headings.
3. **Status** – a new ADR always starts as `proposed`. Only the team sets it to `accepted`
   in the weekly architecture slot. If it replaces an older ADR, set the old one to
   `superseded by ADR-<number>` and mention it.
4. **Context** – describe the problem and the forces neutrally, with facts (tickets, incidents,
   numbers). Don't argue for the solution yet.
5. **Decision** – one decision, in active voice ("We reject ..."), with the concrete values
   and where they live (e.g. constants in `config.py`).
6. **Alternatives** – at least two alternatives that were considered, each with the reason
   why it was not chosen.
7. **Consequences** – positive **and** negative consequences, including what clients have to change.

Keep the ADR short: one page. Return it as Markdown in a code block, together with the file name.
