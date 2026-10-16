# Add skills and tools

This guide shows the three ways to give the agent more knowledge or more
abilities: skills (reusable instructions), a project's `AGENTS.md` (facts
about one project), and custom tools (new actions, written in Python).

## Skills

A skill is a short Markdown file with instructions, such as "how we write
pytest tests". The agent receives a skill when it is relevant to the task.
Certo decides this with simple rules, without an extra model call.

### Built-in skills

Certo ships with skills that load in every run:

- **Eight lifecycle skills**, for every language: `repository-discovery`,
  `requirements-analysis`, `implementation-planning`,
  `testing-and-verification`, `debugging-and-failure-repair`,
  `security-review`, `documentation-and-operational-readiness`,
  `completion-and-release-readiness`. Each one fires on words in the task
  (for example `fix`, `bug` or `traceback` for debugging).
- **Four examples:** `pytest-conventions`, `commit-conventions`,
  `fastapi-conventions`, and `pin-dependencies` (which fires when the agent
  edits `pyproject.toml` or `requirements*.txt`).

A skill only guides the agent. Reading a skill never replaces Certo's own
checks.

### Add your own skills

Put Markdown files in `./skills/` (or the folder named by
`CERTO_SKILLS_DIR`). Subfolders are fine; they only help you organise.
There is no other registration step.

```markdown
---
name: api-conventions
triggers:
  - endpoint
  - api
description: How endpoints are written in our services.
---

Every endpoint returns JSON, validates input with pydantic, and has a test
in tests/api/.
```

How a skill fires depends on its header:

| Header | Fires when |
|---|---|
| `triggers: [...]` | One of the words appears in the task or the conversation (whole word, any case). |
| `paths: [...]` | The agent works on a file that matches one of the patterns. |
| neither | Always. The skill is part of every run. |

A skill of yours with the same `name` as a built-in one replaces it. This
is how you change a built-in skill.

The [AgentSkills](https://agentskills.io/specification) format also works:
a folder with a `SKILL.md` file, placed directly in the skills folder (not
in a subfolder). These skills have no triggers: the agent sees a menu of
them and decides itself when to open one.

### Third-party skills

To use skills published by others, install them with `certo-admin skills`.
They are kept apart from your own skills, and Certo records where each one
came from:

```bash
certo-admin skills install github:anthropics/skills skills/algorithmic-art
certo-admin skills list
certo-admin skills enable algorithmic-art
```

- **Installed is not enabled.** A new skill is off until you run `enable`.
- Files go in `./third_party_skills/` (keep it out of git). A lockfile,
  `./third_party_skills.lock.json`, records the source, the exact commit,
  the license and a hash of every file. You can commit the lockfile so
  others get the same set with `certo-admin skills sync`.
- **Licenses.** Certo recognises a few common open licenses (MIT,
  Apache-2.0, BSD, ISC, MPL-2.0, Unlicense, CC0). Anything else is
  `unknown`, and `enable` refuses it until you add
  `--accept-unknown-license` after reading the terms yourself. This
  detection is a simple text match, not legal advice.
- **Changes turn a skill off.** If `update` brings new content or a new
  license, the skill is disabled again until you re-enable it. A skill
  whose files were changed on disk is skipped.
- Certo never runs a downloaded file. But a skill's text can still ask the
  agent to run its scripts. Read a skill before you enable it. See
  [Safety](../concepts/safety.md#third-party-skills).

Every subcommand is in [Commands](../reference/commands.md#certo-admin-skills).

## `AGENTS.md`: facts about one project

Skills are for knowledge that applies to many projects. For facts about
one project ("this project uses FastAPI and Poetry"), use an `AGENTS.md`
file at the top of the project folder. The agent reads it on every task in
that folder.

Write it yourself, or let Certo write it:

```bash
certo "Add a /health endpoint" --project my-api --agents-md "This project uses FastAPI + Poetry."
```

`--agents-md` replaces the file and needs `--project`. In server mode, send
`agents_md` together with `project`.

## Custom tools

A custom tool gives the agent a new action, written in Python. Certo's own
`run_tests` tool is one. Adding a tool means changing Certo's source, so
work from a checkout of the repository (see
[CONTRIBUTING.md](../../CONTRIBUTING.md)).

Each tool follows the OpenHands SDK pattern of an *Action* (the input), an
*Observation* (the result) and an *Executor* (the code that does the work).
Start from the template, `src/certo/custom_tools/example_tool.py`:

1. Create `src/certo/custom_tools/<name>_tool.py` with an `Action`, an
   `Observation`, a `ToolExecutor`, and a `ToolDefinition` subclass with a
   `create(cls, conv_state, **params)` method. Call
   `register_tool(YourTool.name, YourTool)` at the top level of the module,
   so importing the module registers the tool.
2. Add the tool in `build_tools()` in `src/certo/tools.py`, so the agent
   gets it in local runs.
3. Import the module in `src/certo/custom_tools/__init__.py`, so it is also
   registered in Docker runs. Then rebuild the Docker image.
4. Add `tests/custom_tools/test_<name>_tool.py`: build an `Action`, call the
   executor directly, and check the `Observation`. No model, no network.

Why step 3: in Docker mode the agent runs in a separate process inside the
container. That process only knows the tools it imports when it starts,
and the image starts it with `--import-modules certo.custom_tools`. A tool
that works locally but not in Docker is almost always missing from
`__init__.py`, or the image wasn't rebuilt.

The SDK's own guide: [Custom tools](https://docs.openhands.dev/sdk/guides/custom-tools).

## Related

- [Work on an existing project](work-on-an-existing-project.md)
- [Configuration](../reference/configuration.md)
