# One escalation run: the Wordle sample (Certo 0.1.19)

One real `certo --escalate` run of the sample task `certo init` ships,
`tasks/wordle.md`, with a six-model ladder. It shows what an escalation
run prints when the first model, a local one, finishes the task. It is
one run, not a benchmark: how often a ladder stays local is measured in
[Escalation in 0.1.17](escalation-0.1.17.md).

## The setup

- **Certo:** 0.1.19, from a source checkout. **Run:** 2026-10-19, from
  15:35 UTC, in a new, empty project folder.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 16 GB RAM.
  `qwen3.8:27b` ran on Ollama 0.40.6 on another machine.
- **Settings:** the defaults (checks on, up to 2 fix attempts, 30 minutes
  and 50 steps), plus a cost cap, `CERTO_MAX_TASK_COST=0.50`.
- **Command:**

  ```bash
  CERTO_MAX_TASK_COST=0.50 certo tasks/wordle.md --project wordle --escalate
  ```

The ladder, `default` in `models_list.yaml`:

```text
Escalation: explicit ladder 'default', 6 rung(s):
  1. qwen3.8-27b-local (1 fix attempt(s))
  2. claude-haiku-5-5 (1 fix attempt(s))
  3. claude-sonnet-5-5
  4. gpt-6-luna (1 fix attempt(s))
  5. claude-opus-5-5
  6. gpt-6.1-sol
```

## What it printed

The banner, then, after the agent's work, the end of the run. The folder
path is shortened; nothing else is changed:

```text
── Certo 0.1.19 ────────────────────────────────────────────
  Model    escalate: qwen3.8-27b-local → claude-haiku-5-5 → claude-sonnet-5-5 → gpt-6-luna → claude-opus-5-5 → gpt-6.1-sol
  Folder   …/projects/wordle (project wordle)
  Runs on  this computer
  Checks   on, up to 2 fix attempts
  Limits   30 min · 50 steps · $0.50
────────────────────────────────────────────────────────────
[… 16 minutes of agent work …]
Verification: verified

Run summary:
  Total running time: 16m 00s
  Models: ollama/qwen3.8:27b
  Total tokens: 554,997 (input 536,968, of which cached 0; output 18,029)
  Total cost: $0.0000
  Rungs:
    1. qwen3.8-27b-local (ollama/qwen3.8:27b): verified, 0 fix attempts, 16m 00s, 554,997 tokens, $0.0000
  Final result from rung 1 (qwen3.8-27b-local).
```

## What it shows

- **The first rung finished, so no other model was called.** The local
  model wrote the game (`wordle.py`, `wordle_logic.py`), its tests and a
  README; its 5 tests passed, and the verdict was `verified` with no fix
  attempt. The five cloud rungs never ran, and the run cost $0.00.
- **It took 16 minutes.** The same task took `claude-sonnet-5-5` 48.5s
  in [First run in 0.1.19](first-run-0.1.19.md). Running locally trades
  time for money and privacy.
- **The run left its records.** `.certo/RUNS.md` names the model and the
  rung that gave the result, `MODEL_DECISIONS.md` the ladder and why the
  climb stopped, and the project's `README.md` ends with the note
  "Generated with Certo, using `ollama/qwen3.8:27b`".

## Limits

One task, one run. A different task, or the same one on another day, can
end on a later rung. This run doesn't show a climb; the 0.1.17
escalation run has 10 of them, all past a model that did no work.
