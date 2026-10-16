# Certo v0.1.9

Run each task on the cheapest model that can do it, and prove the result.

## Changed: `activated: false` now applies to `certo bench`

`activated: false` in `models.yaml` now means Certo never uses that model,
in every command. **A `certo bench` arm that names an inactive model is now
an error** (before, the benchmark ignored the flag). If an existing
`bench.yaml` stops with `model 'x' has 'activated: false'`, set
`activated: true` on that model.

## New

- **Escalation between models: `certo --escalate [LADDER]`.** A task
  starts on the first rung of a ladder of models from `models.yaml`,
  typically a free local one. Only when Certo's verdict shows that model
  couldn't finish (`retry_exhausted`, `no_progress`, `timed_out`,
  `incomplete`, `stuck`) does the task move to the next, stronger model, in
  the same folder. `verified` stops at once; `inconclusive` never climbs,
  because there is nothing to act on.
  - **Explicit or derived ladders.** Write ladders under
    `escalation.ladders` in `models.yaml`, or let Certo build one from the
    active models' ratings: least capable first, at most three rungs by
    default. The ladder is printed before the run.
  - **A fresh conversation per rung.** The next model gets the files as
    they are, the original task, the real failing check output, and a short
    note Certo writes from what it recorded. Never the previous model's
    whole conversation.
  - **Limits.** The time budget covers every rung. New
    `CERTO_MAX_TASK_COST` caps what a run may spend (unknown prices count
    as 0). With `--interactive`, Certo asks before each climb, with the
    cost so far.
  - **Visible.** One line per climb, one line per rung in the run summary,
    the ladder and every climb in `MODEL_DECISIONS.md`, a folder per rung
    in the run records, and a `rungs` list in server results.
  - Also as `CERTO_MODEL_SELECTION=escalate` (with
    `CERTO_ESCALATION_LADDER`), and as an `escalate` field on
    `POST /tasks` and the WebSocket. Works in Docker mode.
- **`certo check` checks `models.yaml`**: active and inactive models, each
  ladder, the derived ladder, and every error and warning.
  **`certo check --models`** also sends a real test request to every
  active model, so a broken key shows up before a run.
- **One set of checks for `models.yaml`**, used by `--auto-model`,
  `--escalate`, `certo bench` and `certo check`, with messages that name
  the model or ladder at fault.
- **`strategy: escalate` in `certo bench`**, with an explicit list of
  models or a derived ladder per task. `results.md` gains **cost per
  solved task** for every arm, and for escalate arms **which rung produced
  the final result**.

## Good to know

- Escalation is opt-in: without `--escalate`, runs behave as before.
- It can't be combined with `--auto-model`, `--model` or `--resume`.
- In Docker mode a provider failure can't be told apart from another run
  error; either one moves the task to the next rung.
- Server mode with a SQL task store adds a `rungs` column to the existing
  table on startup.
- Escalation hasn't been benchmarked on real models yet. Measure it on
  yours with `certo bench` before relying on it.

Guide: [Escalate between models](../guides/escalate-between-models.md).
