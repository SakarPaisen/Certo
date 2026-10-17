# Benchmark models and strategies

This guide shows how to measure which models really deliver with Certo,
using `certo bench`: a set of small coding tasks, each graded by tests the
agent never sees. It is for anyone choosing a model, or checking that a
change to Certo makes results better and not worse.

## What it measures

`certo bench` runs the normal Certo pipeline on every task, for every arm
you compare (an arm is a model, used in a certain way), several times.
After each run it grades the result with the task's **hidden tests**.

The tests are hidden because the agent writes its own tests, and Certo
checks the work with them. An agent that misunderstands a rule usually
writes tests with the same misunderstanding, so its own tests pass. Hidden
tests, written with the task, don't share that mistake. They answer two
questions:

1. **How often does each model produce correct code?** The hidden-test
   pass rate.
2. **How often is Certo itself right?**
   - *Fooled:* Certo said `verified`, but the hidden tests failed.
   - *Caught:* the agent claimed it was done, and Certo did not say
     `verified`.

## The tasks

Nine small tasks ship with Certo (task set version 1). Each takes a few
minutes for a capable model; the tricky ones are where smaller models
often go wrong.

| Task | Language | What it tests |
|---|---|---|
| `temperature-table` | Python | An inclusive range with negative steps and a direction check: off-by-one traps. |
| `wordle-score` | Python | Wordle scoring with repeated letters: "correct" first, then "present" only while copies remain. |
| `pedestrian-crossing` | Python | A traffic-light state machine: minimum green time, presses during yellow or red, exact tick counts. |
| `duration-parser` | Python | Parsing `1h30m`-style durations strictly (order, no spaces inside a part) and formatting them back. |
| `page-ranges` | Python | Print page ranges (`1-3,5,7-`) with open ends, overlaps and bounds, and the shortest spec back. |
| `inventory-fix` | Python | Fixing and extending existing code without breaking its tests: validation, a custom exception, no partial changes. |
| `slugify` | Node | URL slugs: removing accents, and shortening without cutting a word. |
| `token-bucket` | Node | A rate limiter with a fake clock: fractional refill, the cap, a clock going backwards. |
| `semver-order` | Node | Version ordering with prereleases: numbers compared as numbers, numeric before text, shorter first. |

`certo bench --list-tasks` lists them. Node tasks need Node 18 or newer.

## How the model files and `bench.yaml` relate

- **`models_list.yaml`** describes the models and **`models.yaml`** holds
  your keys and the models you use: the same two files `--auto-model`
  uses. See [models.yaml and models_list.yaml](../reference/models-yaml.md).
- **`bench.yaml`** says what to compare. Each arm names a strategy and
  models **by their `name`**. It holds no keys, so you can commit it.

The benchmark never reads `.env` and never uses `--auto-model` ranking. An
arm can only name a model that `models.yaml` enables: a model missing
there, or with `activated: false`, is an error. (Before version 0.1.9 the
benchmark ignored `activated`.)

```yaml
# bench.yaml
tasks: all
repeats: 3
arms:
  - name: qwen-local
    strategy: single
    model: qwen3-coder-local      # a model name
  - name: sonnet
    strategy: single
    model: claude-sonnet-5
```

`strategy: single` means one model and the normal Certo run, exactly what
`certo "<task>"` does. `strategy: escalate` climbs a ladder of models,
like `certo --escalate`: give it `models: [a, b]` for a fixed ladder, or no
`models` for the ladder Certo derives from the ratings. Start from
[bench.yaml.example](../../bench.yaml.example); every field is in the
[bench.yaml reference](../reference/bench-yaml.md).

## Run it

```bash
certo bench                     # reads ./bench.yaml and the model files
```

Before anything runs, Certo prints the plan: tasks × arms × repeats, and a
rough cost estimate for paid models where LiteLLM knows the price. Answer
`y` to start, or pass `--yes` (needed when there is no terminal).

**The cost estimate.** Each run is priced at about 500k input and 20k
output tokens, from LiteLLM's price list; local models cost nothing. It is
rough: real runs vary a lot.

- An `escalate` arm is shown with **at most** the cost of every rung
  running. A derived arm lists only the ladder it will use (the same for
  every task), not every active model.
- Most escalation runs stop before the top rung. When earlier results in
  the same parent folder (`bench-results/` by default) include the lower
  rungs' models, the plan also shows a **likely** cost: each rung's cost
  times the share of earlier runs that climbed past the rungs below it. A
  model counts only with the same model id, and both single-model arms and
  escalation rungs count.
- With no such results, only "at most" is shown, with the models that have
  no history.

For example (no earlier results yet):

```text
  derived: escalate, qwen3.8-27b-local (ollama/qwen3.8:27b, local, no cost); claude-haiku-5-5 (anthropic/claude-haiku-5-5, ~$0.30 per run); claude-opus-5-5 (anthropic/claude-opus-5-5, ~$2.40 per run), 9 run(s) (derived from the ratings, the same for every task; at most ~$2.70 per run if every rung runs; no earlier results for qwen3.8-27b-local, claude-haiku-5-5 to say more)
  Estimated cost: at most ~$70.20 (rough: assumes ~500k input and ~20k output tokens per run)
```

`--max-cost` (below) works on the recorded cost, not on the estimate.

**A local model.** Make one arm with an Ollama model enabled in `models.yaml`.
Runs go one at a time, because a local server serves one model at a time.
Give Ollama a large context window first; see
[Ollama and local models](ollama-and-local-models.md).

**A cloud model.** Make one arm with a cloud entry. To keep spending in
check, add a cap; Certo stops starting new runs once the recorded cost
reaches it, and keeps the results so far:

```bash
certo bench --max-cost 5
```

When every arm uses cloud models, runs can go in parallel:
`certo bench --parallel 4`. Certo refuses `--parallel` if any arm runs
locally.

**Both.** Put a local arm and a cloud arm in the same file. This is how to
check the project's rule that changes for local models must not make cloud
models worse.

**Interrupted?** Finished runs are kept. Continue with:

```bash
certo bench --resume            # the latest results folder
certo bench --resume --out bench-results/20261016-101500
```

`--resume` refuses a folder made with different tasks, arms, repeats or
models.

### What each run does

1. A fresh temporary folder gets only the task's starter files. The task
   text is the prompt; `task.md`, the hidden tests and the reference
   solution are never in the folder.
2. The arm's strategy runs the normal Certo pipeline there, with the arm's
   model, including Certo's checks and retries. Certo's default limits
   apply (50 steps per run, 2 fix attempts, 30 minutes), and only its
   built-in skills load, so your own skills can't change the result.
3. The hidden tests are copied in and run in the project's own
   environment. Only they decide the score.
4. The result is saved at once, with a copy of the final folder.

## Read the results

Each benchmark writes a folder, by default `bench-results/<date-time>/`:

| File | What it holds |
|---|---|
| `results.md` | The summary to read and share. |
| `results.csv` | One row per run, for a spreadsheet. |
| `cost.json` | The real total cost, the cost per model, and the plan's estimate. |
| `runs/*.json` | Every detail of each run. |
| `workspaces/<run>/` | The code each run left behind (without `.venv` and `node_modules`). |
| `meta.json` | Certo version, date, hardware, task set, the benchmark itself, and the plan's cost estimate. |

In `results.md`, per arm:

- **Hidden tests passed:** the score, as `passed/total` and a percentage.
- **Verified:** how often Certo said `verified`.
- **Fooled:** Certo said `verified`, but the hidden tests failed. This
  should be close to zero; each one is worth a look.
- **Caught:** the agent claimed it was done, and Certo did not say
  `verified`. Without Certo, each of these would have looked finished.
- **Unconfirmed passes:** Certo did not say `verified`, but the hidden
  tests passed, for example because the agent wrote no tests. Some
  "caught" runs are in fact unconfirmed passes.
- **Median time, tokens and cost.**
- **Cost per solved task:** the arm's total cost divided by the runs whose
  hidden tests passed. The fair way to compare a cheap model that solves
  less with an expensive one that solves more.

A per-task table shows where each arm passes and fails. For `escalate`
arms, a section shows how often each rung produced the final result,
for example `rung 1 (qwen-local): 4/9, rung 2 (gpt-luna): 5/9`.

**The real cost.** The **Cost** section of `results.md` (and `cost.json`)
gives what the benchmark really spent, from the recorded runs, next to what
the plan estimated, and one row per model: its runs, its cost, and its
average per run. An escalation run is split by rung, so each model is
charged only for what it ran. The same total is printed at the end:

```text
Total cost: $1.5000 (the plan estimated at most ~$9.00, likely ~$3.50), for 3 of 12 runs
```

Costs come from LiteLLM's prices; `+ unknown` means a model had no price.
When the benchmark is not finished, the line says how many runs it covers,
as above.
A results folder from before version 0.1.13 has no estimate to compare.

**Keep the numbers in proportion.** With 9 tasks and 3 repeats, an arm has
27 runs; a difference of two or three runs can be chance. Compare results
only when the task set version and hash in the header match.

## Add a task

A task is a folder:

```text
my-task/
  task.md        the prompt the agent sees
  starter/       optional starting files the agent sees
  hidden_tests/  the tests that decide the score; never shown to the agent
  reference/     a reference solution; never shown to the agent
```

- Python hidden tests are pytest files (`test_*.py`) that import the
  solution's modules by name. Node hidden tests are `*.test.js` files for
  `node --test` that `require('../module.js')`.
- `task.md` must state everything the hidden tests check: file names,
  function names, errors, edge cases. A test that checks something the
  prompt doesn't ask for measures luck, not skill.
- Ask for the agent's own tests in `task.md`, so Certo has something to
  verify.

Put your tasks in a folder of their own and point `tasks_dir` in
`bench.yaml` at it. Then check them, with no model:

```bash
certo bench --check-tasks
```

Every reference solution must pass its hidden tests, and every starter
alone must fail them.

To add a task to the bundled set, work from a checkout (see
[CONTRIBUTING.md](../../CONTRIBUTING.md)): add the folder under
`src/certo/benchmark_tasks/`, raise the number in its `VERSION` file, and
run the test suite, which checks every task the same way.

## Related

- [bench.yaml reference](../reference/bench-yaml.md)
- [Commands: certo bench](../reference/commands.md#certo-bench)
- [How verification works](../concepts/how-verification-works.md)
