---
name: triage-bug-ticket
description: Triages a bug report for Roomie - assesses severity, finds the affected code and suggests the next steps. Use it when a developer asks to analyse, assess or prioritise a bug ticket or an error report.
---

# Triage a bug ticket

Team Workplace triages new bugs every morning. The result of a triage is a short,
structured comment on the ticket.

## Severity levels of Team Workplace

| Level | Meaning | Reaction |
|---|---|---|
| **S1** | Nobody can book rooms, or data of other users is exposed | Fix immediately, inform `#facility-roomie` |
| **S2** | A core function fails for a group of users (e.g. one client, one office) and there is no workaround | Fix in the current sprint |
| **S3** | A function fails, but there is a workaround | Plan for the next sprint |
| **S4** | Cosmetic or rare edge case | Backlog |

A 500 response is never "expected behaviour" (API-06), but it is not automatically S1 –
check whether there is a workaround.

## Steps

1. **Reproduce in thought** – which request, which user role, which data? If the report is too
   vague, list the missing information instead of guessing.
2. **Find the rule** – which guideline, ADR or error code defines the correct behaviour?
3. **Locate the code** – name the module and function that most likely causes the bug
   (routers → services → repository).
4. **Check the runbook** – `docs/runbook.md` may already describe the problem and a workaround.
5. **Assess** – severity (table above), affected clients, workaround.

## Output format

```
Severity: S<n> – <one-sentence reason>
Expected behaviour: <rule or ADR>
Suspected cause: <module.function> – <why>
Workaround: <workaround or "none">
Next steps:
1. <regression test (see skill write-regression-test)>
2. <fix>
Open questions: <or "none">
```
