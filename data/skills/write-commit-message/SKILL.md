---
name: write-commit-message
description: Writes a git commit message for a change, following the commit conventions of Team Workplace (Conventional Commits, ticket reference, AI trailer). Use it whenever the developer asks for a commit message or wants to commit changes.
---

# Write a commit message

Our commit messages follow GIT-02 (Conventional Commits). The changelog of every
release is generated from them (GIT-06), so they are read by people outside the team.

## Format

```
<type>(<scope>): <summary>

<body>

Refs: <ticket id>
Assisted-by: <name of the AI assistant>
```

## Steps

1. **Type** – choose exactly one of `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.
   A bug fix together with its regression test is a `fix`, not a `test`.
2. **Scope** – the affected area of Roomie in lowercase, usually the module or router name:
   `bookings`, `rooms`, `availability`, `notifications`, `auth`, `scheduler`, `config`.
3. **Summary** – imperative mood, lowercase, no period at the end, at most 72 characters
   including type and scope. Describe the behaviour, not the code:
   - good: `fix(bookings): reject timestamps without timezone offset`
   - bad: `fix(bookings): add tzinfo check to validate_new_booking`
4. **Body** – explain **why** the change is needed and what the user-visible effect is.
   Wrap lines at 72 characters. Leave it out only for trivial changes (typos, formatting).
5. **Footer**
   - `Refs: WORK-123` – the Jira ticket. Every commit needs one; ask the developer if it is unknown.
   - `BREAKING CHANGE: ...` – if clients have to change something (see API-01).
   - `Assisted-by: <assistant>` – **always add this trailer when you (the AI assistant)
     wrote or substantially changed the code or the message.** We use it to evaluate
     AI-generated code in reviews (GIT-05).

## Checklist

- [ ] One logical change per commit – suggest splitting if the diff mixes several changes.
- [ ] New error codes or changed business rules (`config.py`) are mentioned in the body,
      because they need extra approvals (GIT-04).
- [ ] No secrets, user ids or meeting titles in the message (SEC-04, DP-01).

Return only the commit message in a code block, followed by at most two sentences of explanation.
