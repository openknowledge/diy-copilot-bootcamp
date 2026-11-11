# AI Assistant Usage Policy

- Owner: Information Security, Engineering Guild, Data Protection Officer
- Applies to: all employees using AI assistants for software development
- Version: 1.1

AI coding assistants can make us faster, but they also introduce new risks.
This policy defines how they may be used.

## AI-01 – Approved tools

Only AI assistants approved by Information Security may be used with company
code. Approved tools are configured so that our prompts and code are **not
used for training** by the provider. The list of approved tools is
maintained in the intranet. Using private accounts of AI tools for company
work is not allowed.

## AI-02 – What must not be shared with AI assistants

- Secrets of any kind (see SEC-01) – remove them before you paste code or logs.
- Personal data of employees or customers (see DP-06), e.g. production logs
  with user ids, booking data, meeting titles.
- Code or documents classified as **confidential** (e.g. security concepts,
  unreleased financial data).

Internal code of normal classification may be shared with approved tools.

## AI-03 – Responsibility

The developer who commits AI-generated code is responsible for it. AI output
is reviewed like any other code (see GIT-05) and must follow all coding,
testing and security guidelines. "The AI wrote it" is not an excuse.

## AI-04 – Verification

Do not trust AI answers about our internal systems, business rules or
guidelines without checking the source. AI assistants without access to our
knowledge base invent plausible but wrong answers.

## AI-05 – Agents and tool use

AI agents that can execute commands or change files may only be used:

- in a sandbox or on a feature branch, never directly on `main`,
- without access to production credentials,
- with a human approving every change before it is merged.

Agents must not be allowed to push to remote repositories, deploy, or call
production APIs on their own.

## AI-06 – Licensing

Do not accept AI suggestions that reproduce large parts of existing code
verbatim if the license is unknown. Enable the "public code filter" of the
assistant where available.

## AI-07 – Reporting

Report incidents (e.g. a secret was accidentally sent to an AI tool) to
`#security` immediately.
