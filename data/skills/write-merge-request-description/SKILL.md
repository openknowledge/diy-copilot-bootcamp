---
name: write-merge-request-description
description: Writes the description of a merge request (pull request) for a change in a repository of Team Workplace, including test evidence and the required approvals. Use it when the developer wants to open a merge request or asks for a PR/MR description.
---

# Write a merge request description

A merge request description is read by the reviewers (GIT-03, GIT-04) and later by people
who search for the reason of a change. It must answer: why, what, how tested, who has to approve.

## Steps

1. Read the template `assets/template.md` of this skill and fill in **every** section.
   Don't remove sections – write "n/a" with a short reason instead.
2. **Title** – `<ticket id>: <summary of the change>`, e.g. `WORK-412: Reject timestamps without timezone offset`.
3. **Why** – the problem from the user's perspective. Link the ticket. Quote the guideline or
   ADR the change implements (e.g. API-07, ADR-0004).
4. **What changed** – a short list of the changes per layer (router, service, config, tests,
   docs). Mention new or changed error codes explicitly – they are part of the API contract (API-05).
5. **How it was tested** – the regression test (TEST-07) and how to reproduce the problem
   manually (e.g. a `curl` call). Never paste real API keys; use `$ROOMIE_KEY`.
6. **Required approvals** – derive them from GIT-04:
   - always: one member of Team Workplace
   - changes to business rules in `config.py`: product owner of facility management
   - changes to authentication, authorization or personal data: security champion
7. **Size** – if the diff has more than 400 changed lines, suggest splitting it (GIT-03).
8. If an AI assistant generated code, tick the corresponding checkbox (GIT-05).
