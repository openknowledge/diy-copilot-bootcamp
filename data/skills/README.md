# Skills of Team Workplace

Skills are reusable instructions for the coding assistant: *how* the team does
recurring tasks (commit messages, merge requests, regression tests, ...).
The *rules* themselves live in the knowledge base (`data/knowledge_base`);
skills refer to them by their ids (e.g. GIT-02, TEST-07).

Each skill is a folder with a `SKILL.md` file in the
[Agent Skills](https://agentskills.io) format:

```
<skill-name>/
├── SKILL.md      # YAML frontmatter (name, description) + instructions
└── assets/       # optional: templates and other files the skill refers to
```

The assistant only sees the `name` and `description` of every skill. It loads
the instructions of a skill – and its additional files – when it needs them
(progressive disclosure). Used in `day-02/solutions/03_context_engineering`.
