# Certo v0.1.14

A run in which the agent changes nothing is no longer `verified`. This
release also contains [v0.1.13](release-notes-v0.1.13.md),
[v0.1.12](release-notes-v0.1.12.md) and [v0.1.11](release-notes-v0.1.11.md),
which were not published on their own.

## New: the `unchanged` verdict

A project's checks can pass before the agent does anything, for example
when a "fix and extend" task starts from code whose tests already pass.
Certo used to say `verified` there even when the agent changed nothing.
The first complete benchmark found exactly that: a local model ended such
a task without editing a file, Certo said `verified`, and the hidden tests
failed.

Now, after a `verified` run, Certo checks whether any file in the project
folder changed:

- **No file changed:** Certo asks the agent once to do the task, or to
  say why no change is needed. If a file then changes, Certo checks the
  project again as usual.
- **Still no change:** the verdict is `unchanged`.

`unchanged` exits 0, like `inconclusive`, because some tasks really need
no change. `--require-verification` (or `"require_verification": true` in
server mode) makes it exit 1. See
[Verdicts](../reference/verdicts.md#unchanged-in-more-detail).

With `--escalate`, `unchanged` moves the task to the next model, unless
the model before it also ended `unchanged`: then two models agree there is
nothing to change, and the climb stops.

## Fixed

- **A local model's cost is zero, not unknown.** Runs on `ollama/` (and
  other local) models showed `+ unknown` in every total; they now count
  as free. Older benchmark results read the same way when the report is
  written again.
- **A derived escalation arm in `certo bench` shows its ladder** in the
  results, not every active model.

## Good to know

- A resumed run (`certo --resume`) never ends `unchanged`: its changes may
  come from the earlier session.
- Some files never count as a change: Certo's own (`MODEL_DECISIONS.md`,
  `.certo/`), environments, caches and build output.
