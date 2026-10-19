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
