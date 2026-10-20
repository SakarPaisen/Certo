# Certo v0.1.20 (not released yet)

The task profiles and the escalation ladders move out of
`models_list.yaml` into files of their own, a run that uses all its steps
is checked instead of ending `stuck`, a task profile can name the model to
use, `certo check` shows which models your task profiles pick, and
`--auto-model` reads a task's title instead of its whole text.

## Changed: one file per mode for your model choices

`models_list.yaml` used to hold three things: the models, the task
profiles and the escalation ladders. Now it holds only the models. The
other two have their own optional files, one per mode:

| File | Holds | Read by |
|---|---|---|
| `models_list.yaml` | the models: ids, ratings, descriptions | everything |
| `models.yaml` | your keys, addresses, which models are enabled | everything |
| `task_profiles.yaml` | `task_profiles:` | `--auto-model` |
| `escalation.yaml` | `escalation:` (ladders, `cost_axis`, `max_rungs`) | `--escalate`, `certo bench` |

Certo looks for the new files like the other two: the current folder,
then `~/.config/certo/`, or the path in `CERTO_TASK_PROFILES_FILE` /
`CERTO_ESCALATION_FILE` (`escalation_file` in a benchmark file). Both are
optional: without `task_profiles.yaml`, `--auto-model` ranks the models
with no weights; without `escalation.yaml`, `--escalate` builds a ladder
from the ratings. `certo check` lists which ones it found. The examples
Certo ships are now four files.

**Nothing breaks.** A `task_profiles:` or `escalation:` section still in
your `models_list.yaml` keeps working, with a warning at every run that
says where to move it:

```text
.../models_list.yaml has the 'task_profiles:' section. Since 0.1.20 it belongs in its own file, task_profiles.yaml, next to models_list.yaml: move the section there as it is. It is still read for now.
```

To move, cut each section, with its key, into its new file next to
`models_list.yaml`; nothing inside changes. A later version will stop
reading the old sections. See
[The model files](../reference/models-yaml.md#moving-from-one-file-0119-and-earlier).

## Changed: a run that uses all its steps is checked, and can switch model

When the agent used all its steps (`CERTO_MAX_ITERATIONS`, 50 by
default), the run ended `stuck` and Certo checked nothing, even when the
work was done. On 2026-10-19 a run of the Hanoi example ended `stuck` on
its 50th step, right after that step ran 116 passing tests; `certo
verify` afterwards said `verified`.

Now Certo runs the project's checks after such a run, as after a normal
finish:

- the checks pass → `verified`;
- the checks fail → the usual fix attempts, each with a fresh set of
  steps. With `--auto-model`, the next attempt runs on the next model, in
  the same conversation; with `--escalate`, the rung climbs as for any
  failure once its fix attempts are used;
- nothing can be checked → `stuck`, as before.

Any other error still ends `stuck` at once. The time budget and the cost
cap still bound the whole task, so a model can't loop forever. See
[Verdicts](../reference/verdicts.md#the-order-of-the-checks).

## New: a task profile can name its model

`--auto-model` picks a model by scoring every model against the
profile's weights. Now a profile can also say which model to use:

```yaml
task_profiles:
  debugging:
    triggers: [fix, bug, crash, "failing test"]
    model: claude-sonnet-5-5
    weights: {reasoning: 3, precision: 2, code: 2, cost: 0.5}
```

The named model runs first when it is enabled in `models.yaml`; if it
fails, the weights pick the next one. When it isn't enabled, the weights
decide as before, and `MODEL_DECISIONS.md` says why. `certo check` reports
a name that doesn't exist. See
[Pick models automatically](../guides/pick-models-automatically.md#always-use-one-model-for-a-kind-of-task).

## New: see which models your task profiles pick, before a run

`certo check` now lists every task profile, its trigger words, and the
first three models `--auto-model` would try for it, with their scores.
`certo check --task "..."` (text or a task file) shows what one task
would get: its title, the profile it matches and why, and every model in
order. Neither calls a model, so you can tune `task_profiles.yaml` and
check again at no cost. See
[Pick models automatically](../guides/pick-models-automatically.md#preview-and-tune-the-choice).

## Fixed: `--auto-model` reads the task's title, not its whole text

`--auto-model` picks a task profile by looking for trigger words in the
task. It used to search the whole text, including inside longer words, so
almost every task file matched the `debugging` profile of the example
catalog: a spec that says "raise ValueError" contains "error", and "fix
all build failures" contains "fix". With the shipped example catalog, 12
of the 14 task files Certo ships were classified as debugging.

Now Certo looks only at the task's first line with text (a task file's
title, or the whole task when it is one line), and a trigger must be a
whole word, or its plural: "bug" matches "bugs", "fix" no longer matches
"prefix". `MODEL_DECISIONS.md` says which word matched. If your own task
profiles relied on words in the body of a task, put them in its title.
See [Pick models automatically](../guides/pick-models-automatically.md).

## Fixed: a Python project with no manifest is checked from its top folder

Without a `pyproject.toml` (or `setup.py`, `setup.cfg`), Certo used to run
the checks from the first folder with `.py` files it found. For a project
with a `hanoi/` package and a `tests/` folder side by side, that was
`hanoi/`, so pytest found no tests and the verdict was `inconclusive`,
although the project's 79 tests pass. Now the checks run from the folder
that holds both.

A program inside a package now also runs as a module: `hanoi/__main__.py`
runs as `python -m hanoi`, not `python __main__.py` from inside the
package. Run by its path, the package's own imports (`from hanoi.cli
import main`) fail, which had pushed the agent to add a `sys.path`
workaround to pass the check. See
[Verification by language](../reference/verification-by-language.md).

## Fixed: a broken ladder no longer stops `--auto-model`

`--auto-model` never uses escalation ladders, but a ladder problem (such
as a ladder with no enabled model) stopped an `--auto-model` run with an
error. Now a problem in a part of the model files the run doesn't use is
a warning, and the run goes on: ladders for `--auto-model`, a task
profile's `model:` for `--escalate`. `certo check` still reports them as
errors. See [The model files](../reference/models-yaml.md#checks).
