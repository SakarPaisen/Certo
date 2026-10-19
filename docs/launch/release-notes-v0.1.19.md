# Certo v0.1.19

Each project now remembers which models built it. This release also
contains [v0.1.18](release-notes-v0.1.18.md), which was not published on
its own.

## New: `.certo/RUNS.md`, one entry per run

`.certo/STATUS.md` holds only the last run, so a few runs later there was
no way to tell which model wrote a project. Now every `certo` run also
adds an entry to `.certo/RUNS.md`, and old entries are kept:

```text
## 2026-10-19 08:05 UTC · verified

- Task: Build a terminal Wordle game in Python, with pytest tests.
- Certo: 0.1.19
- Model: openai/gpt-5.6-luna
- Time: 4m 03s · Tokens: 801,191 · Cost: $0.0593
```

With `--escalate`, the entry lists every rung that ran, with its model and
verdict. Interrupted runs and runs that stopped with an error are recorded
too. Certo writes the file, never the agent, and it names models, never
keys. Like the rest of `.certo/`, it is ignored by git, and
`CERTO_SAVE_STATE=false` turns it off. See
[Run records and costs](../guides/run-records-and-costs.md#which-model-built-this-project).

## New: the project's README names its models

In a project folder Certo created (`--project` with a new name), Certo now
adds one line at the end of the project's `README.md` after each finished
run:

```text
*Generated with [Certo](https://github.com/alessioricco/certo), using `ollama/qwen3.8:27b`, `anthropic/claude-haiku-5-5`.*
```

It names every model that wrote code there, and a later run updates the
same line. Certo never edits the README of a folder you brought.

## Fixed: server run records under the right project

With `CERTO_ARTIFACTS_DIR` set, runs started through the WebSocket
(`/tasks/stream`) or `/v1/chat/completions` were filed under `_unscoped`
even when the request named a `project`. They are now filed under that
project, as `POST /tasks` already did.

## Fixed: model check messages no longer say ".env"

When `certo check` or `certo init` found a problem, the message said to
fix the setting "in .env", for example "Check CERTO_LLM_API_KEY in .env".
Since 0.1.5 the value usually comes from the user settings file or the
shell instead. The messages now say "in your settings"; `certo check`
shows where each setting comes from.
