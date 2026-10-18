# Auto-model or escalation: two ways to choose models

Certo can choose the model for a task in two ways. Both use your model
files (`models_list.yaml` and `models.yaml`), but they answer different
questions:

- **`--auto-model`** asks: *which model fits this task?* It decides once,
  before the run, from the words in the task.
- **`--escalate`** asks: *how cheaply can this task be done?* It starts on
  a cheap model, and moves to a stronger one only when Certo's
  verification shows the cheap one couldn't finish.

This page explains how each one decides, when to use which, and how to
turn each on. The step-by-step setup is in two guides:
[Pick models automatically](../guides/pick-models-automatically.md) and
[Escalate between models](../guides/escalate-between-models.md).

## Side by side

| | `--auto-model` | `--escalate` |
|---|---|---|
| **The question** | Which model fits this task? | How cheaply can this task be done? |
| **When it decides** | Once, before the run, from the task text | Step by step, after each run, from Certo's verdict |
| **What it uses** | Task profiles: trigger words and weights | A ladder: one you write, or one derived from capability and cost |
| **First model** | The best fit for the task's profile, often an expensive one | The cheapest rung |
| **Changes model when** | The provider fails (rate limit, outage, bad key), or a fix attempt still fails Certo's checks | The model's whole run fails: checks still fail after all its fix attempts, the agent is stuck, out of time, or changed no file |
| **How it changes** | Inside the same conversation: the next model carries on from where the last one was | A new conversation in the same folder, with a note on what the previous model did |
| **Next model** | The next best fit, not necessarily a stronger one | Always the next rung, a stronger one |
| **Cost** | Set by the choice | Low when the cheap model succeeds; more when it climbs |
| **Turn it on** | `--auto-model`, or `CERTO_MODEL_SELECTION=auto` | `--escalate [LADDER]`, or `CERTO_MODEL_SELECTION=escalate` |

Without either one, Certo uses one model: `CERTO_LLM_MODEL`, or `--model`.
The two modes can't be combined: `--escalate` with `--auto-model` or
`--model` is an error, because each one decides the models itself.

## How `--auto-model` decides

1. **It picks a task profile.** Each profile in `models_list.yaml` has
   trigger words. Certo looks for them in the task text, profile by
   profile in the order of the file; the first profile with a match wins.
   With no match, the profile named `default` is used.
2. **It scores every active model.** A model's score is each rating times
   the profile's weight for it, added up.
3. **It runs the model with the highest score.** If the provider fails,
   or a fix attempt still fails Certo's checks, Certo moves to the next
   model in the same order and carries on in the same conversation. The
   order is computed once, so the next model is the next best fit for the
   task, not necessarily a stronger one. (Under `--execution docker`,
   only the first choice works: Certo can't switch models during a run.)

An example with three models:

| Model | reasoning | precision | code | cost |
|---|---|---|---|---|
| local-coder | 1 | 2 | 1 | 5 |
| claude-haiku | 3 | 3 | 4 | 4 |
| claude-sonnet | 4 | 4 | 5 | 2 |

and three profiles: `debugging` (triggers `fix`, `bug`, `crash`; weights
reasoning 3, precision 2, code 2, cost 0.5), `scaffolding` (triggers
`scaffold`, `set up`, `boilerplate`; weights cost 2, code 1, reasoning
0.5, precision 0.5) and `default` (every weight 1):

| Task | Profile | Scores | Runs on |
|---|---|---|---|
| "Fix the crash when the input file is empty" | `debugging` | sonnet 31, haiku 25, local-coder 11.5 | claude-sonnet |
| "Scaffold a FastAPI project" | `scaffolding` | haiku 15, sonnet 13, local-coder 12.5 | claude-haiku |
| "Write a Wordle game in Python" | `default` | sonnet 15, haiku 14, local-coder 9 | claude-sonnet |

Two things follow from how it works:

- **Matching is plain text.** "Handle errors gracefully" contains "error",
  so a `debugging` profile with that trigger matches it. Pick trigger
  words with care, and remember that the first matching profile wins.
- **The `default` profile decides most tasks.** Many tasks match no
  trigger. With equal weights, cost is one axis out of four, so the
  strongest model usually wins. Give `cost` a higher weight in `default`
  if you want cheap models for everyday tasks.

## How `--escalate` decides

1. **It takes a ladder.** `--escalate NAME` uses the ladder with that name
   in `models_list.yaml`. Plain `--escalate` uses the ladder named
   `default`, and when there is none, a ladder Certo derives from the
   ratings.
2. **It runs the first rung** as a normal Certo run, with its fix
   attempts.
3. **It reads the verdict.** `verified` ends the task. A verdict that says
   the model couldn't finish (`retry_exhausted`, `no_progress`,
   `timed_out`, `incomplete`, `stuck`), `unchanged` (the model changed no
   file) or a provider failure moves the task to the next rung. The next model starts a new conversation in the
   same folder, with the files as they are, the failing checks, and a note
   from Certo on what the previous model did.
4. **It stops** at `verified`, at a verdict that gives no reason to climb
   (`inconclusive`, `budget_exhausted`, `confirmation_required`), when two
   rungs in a row end `unchanged`, or after the last rung.

The full list of verdicts and what each does is in
[Escalate between models](../guides/escalate-between-models.md#what-makes-certo-climb).

With the same three models, the derived ladder is:

```text
Escalation: derived ladder (from the ratings), 3 rung(s):
  1. local-coder (capability 4, cost rating 5)
  2. claude-haiku (capability 10, cost rating 4)
  3. claude-sonnet (capability 13, cost rating 2)
```

Every task starts on local-coder, whatever its words. A task it solves
costs nothing. A task it can't finish moves to claude-haiku, then
claude-sonnet.

## When to use which

**Use `--escalate` when:**

- You have a local or cheap model that can do much of your work, and
  want to pay for a strong model only when it can't. This is the main
  use case.
- The project has tests or a build that Certo can run. Escalation climbs
  on Certo's verdict, so it needs something to verify. A project with
  nothing to check ends `inconclusive` and never climbs.
- You run many tasks unattended (a batch, a benchmark, CI) and want the
  total cost low without picking a model per task.

**Use `--auto-model` when:**

- The kind of task clearly decides the model, and the cheap model is
  certain to fail on some kinds. For example, design or research tasks
  that you always want on a strong model: escalation would spend time
  on the cheap rung first.
- There is little or nothing for Certo to verify, such as writing
  documentation or an analysis. `--auto-model` doesn't need a verdict to
  choose.
- You want automatic fallback when a provider is down, with a model
  chosen for the task.
- You want a model switch to keep the conversation. With `--auto-model`
  the next model sees everything the last one did; an escalation rung
  starts fresh, with Certo's note.

**Use one model** (`CERTO_LLM_MODEL`, or `--model`) when you already know
which model you want, or when you compare models one by one.

**Not sure?** Measure it. `certo bench` runs the same tasks with each
strategy and reports how many it solved and what it cost. See
[Benchmark models and strategies](../guides/benchmark.md).

## Use cases

| Situation | Choice | Why |
|---|---|---|
| A local model on your machine, a cloud key for hard cases | `--escalate` | Free when the local model succeeds; the cloud model only for what it can't finish |
| Fixing bugs in a project with a good test suite | `--escalate` | Failing tests are exactly the signal escalation climbs on |
| Generating boilerplate or a new project skeleton | `--auto-model` with a `scaffolding` profile that weighs cost, or `--escalate` | Either keeps it on a cheap model; escalation also checks the result |
| An architecture or design task | `--auto-model` with a profile that weighs reasoning | A cheap first rung would likely fail and cost time |
| Writing documentation, nothing to test | `--auto-model` | No verdict for escalation to act on |
| Many tasks overnight, cost matters | `--escalate`, with `CERTO_MAX_TASK_COST` | Climbs only when needed, with a cap per task |
| A provider that is often rate-limited | `--auto-model` | Moves to the next model when the provider fails |

## Turn each one on

`--auto-model`, for one run:

```bash
certo --auto-model "Fix the crash when the input file is empty"
```

With `--interactive` as well, Certo shows the ranked models and lets you
confirm or change the choice before it starts. Every choice and the reason
for it is written to `MODEL_DECISIONS.md` in the project folder.

`--escalate`, for one run:

```bash
certo --escalate "Fix the crash when the input file is empty"
certo --escalate hard "Rewrite the parser"    # the ladder named "hard"
```

The ladder is printed before the run starts, and each step is written to
`MODEL_DECISIONS.md`.

For every run, put the mode in your settings file instead:

```dotenv
# auto or escalate
CERTO_MODEL_SELECTION=escalate
```

Before a run, `certo check` shows your model files, the active models,
each ladder and the ladder Certo would derive, with any problems found.

## Related

- [Pick models automatically](../guides/pick-models-automatically.md):
  set up `models_list.yaml`, `models.yaml` and task profiles.
- [Escalate between models](../guides/escalate-between-models.md):
  ladders, budgets and what makes Certo climb.
- [`models_list.yaml` and `models.yaml`](../reference/models-yaml.md):
  every field.
- [How verification works](how-verification-works.md): where the verdict
  that escalation acts on comes from.
