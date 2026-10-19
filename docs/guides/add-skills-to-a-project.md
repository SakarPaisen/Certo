# Add skills to a project

This guide shows how to give the agent instructions that belong to one
project: its conventions, its commands, the things it should never do.
They live in the project folder, travel with it (you can commit them),
and apply to every task Certo runs there. For skills you want in every
project, see [Add skills and tools](add-skills-and-tools.md).

## Where they go

| What | Where, in the project folder | When the agent gets it |
|---|---|---|
| Facts about the project | `AGENTS.md` | In every task |
| Skills for this project | `.agents/skills/` | When the skill fires (see below) |

Certo finds both in the folder the agent works in: the folder you run
`certo` from, or `projects/NAME` with `--project NAME`. Nothing needs to
be registered or configured.

## Facts: `AGENTS.md`

Write what every task in the project should know, in plain words:

```markdown
This project uses FastAPI and Poetry.
Run the tests with `poetry run pytest`.
Never edit files under migrations/ by hand.
```

Or let Certo write it when it starts a task:

```bash
certo "Add a /health endpoint" --project my-api --agents-md "This project uses FastAPI and Poetry."
```

`--agents-md` replaces the file and needs `--project`. A project that
already has a `CLAUDE.md`, `GEMINI.md` or `.cursorrules` file for another
tool works as it is: those are read the same way as `AGENTS.md`.

## Skills: `.agents/skills/`

A skill is a Markdown file with a short header. Put one file per skill
in `.agents/skills/` at the top of the project:

```text
my-api/
├── AGENTS.md
└── .agents/
    └── skills/
        ├── api-conventions.md
        └── release-checklist/
            └── SKILL.md
```

A skill that fires on words in the task, `.agents/skills/api-conventions.md`:

```markdown
---
name: api-conventions
triggers:
  - endpoint
  - api
description: How endpoints are written in this project.
---

Every endpoint returns JSON, validates its input with pydantic, and has a
test in tests/api/.
```

The header decides when the agent gets the skill:

| Header | The agent gets the skill when |
|---|---|
| `triggers: [...]` | one of the words appears in the task or the conversation (whole word, any case) |
| `paths: [...]` | it works on a file that matches one of the patterns |
| neither | always |

A skill can also be a folder with a `SKILL.md` file, in the
[AgentSkills](https://agentskills.io/specification) format, like
`release-checklist/` above. Such a skill has no triggers: the agent sees
a list of these skills and opens one when it decides it needs it.

## Good to know

- **Project skills win.** A project skill with the same `name` as one of
  Certo's built-in skills, or one of your own in `CERTO_SKILLS_DIR`,
  replaces it for this project. This is how a project changes a built-in
  skill, such as `pytest-conventions`.
- **In a git repository, the top of the repository counts too.** When the
  agent works in a subfolder, it also gets the `AGENTS.md` and
  `.agents/skills/` at the repository's root. Where both have a skill of
  the same name, the subfolder's wins.
- **`./skills` is not the project's folder.** `CERTO_SKILLS_DIR` (by
  default `./skills`) is relative to the folder where you run `certo`. With
  `certo ... --project my-api` run from a workspace, that is the
  workspace's `skills/`, not `my-api/skills/`. For skills that belong to
  one project, use `.agents/skills/`.
- **The agent can read and change these files**, because they are in the
  folder it works in. Commit them, so you see any change in `git diff`.
- **Skills guide; they don't check.** A skill tells the agent what to do.
  Whether the result works is still decided by Certo's own checks.
- **Docker execution (experimental):** project skills haven't been checked
  under `--execution docker`.

## Related

- [Add skills and tools](add-skills-and-tools.md): Certo's built-in
  skills, skills for every project (`CERTO_SKILLS_DIR`), third-party
  skills and custom tools
- [Work on an existing project](work-on-an-existing-project.md)
- [Configuration](../reference/configuration.md#skills): `CERTO_SKILLS_DIR`
