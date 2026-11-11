# Developer Onboarding

- Owner: Engineering Guild
- Last updated: September 2026

Welcome! This page helps you to get started as a developer in our company.

## Week 1 checklist

- [ ] Pick up your laptop and hardware key at the IT service desk.
- [ ] Set up MFA for your company account (see the access policy).
- [ ] Install the password manager and the VPN client.
- [ ] Request access to GitLab, Jira and the CI system via the access portal.
- [ ] Join the Slack channels of your team and `#engineering`,
      `#security` and `#dev-help`.
- [ ] Read the engineering guidelines (coding, API design, testing, git).
- [ ] Complete the mandatory trainings on data protection and security
      awareness in the learning portal (deadline: end of week 2).

## Development environment

- Laptops run macOS or Ubuntu; Windows only with WSL.
- Python services use `uv`, Java services use Gradle.
- Docker Desktop is licensed; Podman is an allowed alternative.
- The internal package mirror must be used for Python and npm packages. The
  configuration is installed automatically by the setup script
  `dev-setup.sh` in the GitLab project `platform/dev-setup`.

## Approved AI assistants

The approved AI coding assistants and how to request a licence are listed in
the intranet. Read the AI assistant usage policy before you start.

## Your first contribution

Every new developer gets a "good first issue" in their team. Pair with your
onboarding buddy for your first merge request.

## Who to ask

- Your onboarding buddy (assigned by your team lead)
- `#dev-help` for technical questions
- IT service desk for hardware and accounts: `#it-help`
