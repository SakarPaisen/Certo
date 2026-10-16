# bench.yaml

The format of the benchmark file read by `certo bench`. It is for looking
things up; the guide is [Benchmark models and strategies](../guides/benchmark.md).

The default file is `./bench.yaml`; `certo bench --config FILE` reads
another. It holds no keys: models are named from `models.yaml`. A commented
example ships as [bench.yaml.example](../../bench.yaml.example).

## Layout

```yaml
models_file: ./models.yaml   # optional
tasks_dir: ./my-tasks        # optional
tasks: all                   # or a list of task names
repeats: 3
arms:
  - name: qwen-local
    strategy: single
    model: qwen3-coder-local
```

## Top-level keys

| Key | Default | Meaning |
|---|---|---|
| `arms` | **required** | A non-empty list of arms (below). |
| `tasks` | `all` | `all`, or a list of task names. `certo bench --list-tasks` shows the names. |
| `repeats` | `1` | Runs per task per arm, a whole number of at least 1. Results vary between runs, so more repeats give a fairer comparison. |
| `models_file` | `./models.yaml` | The model catalog the arms name models from. |
| `tasks_dir` | the bundled task set | A folder of your own tasks, in the same shape. |

Any other key is an error. Relative paths are relative to the folder where
you run `certo bench`.

## Arms

Every arm has:

| Key | Meaning |
|---|---|
| `name` | A unique name, made of letters, digits, `.`, `_` and `-`. It appears in the results and in file names. |
| `strategy` | How the arm runs a task. See below. |

The other keys depend on the strategy. An unknown strategy, or a key the
strategy doesn't take, is an error that lists what is allowed.

### `strategy: single`

One model, the normal Certo run: exactly what `certo "<task>"` does.

| Key | Meaning |
|---|---|
| `model` | The `name` of an entry in the models file. An unknown name is an error that lists the names the file has. |

## How models are used

- The arm's model is taken from its `models.yaml` entry: `model`,
  `api_key`, `base_url` and `reasoning_effort`. An empty field stays empty;
  it is never filled from `.env` or the environment's `CERTO_LLM_*`
  settings.
- An arm that names a model with `activated: false` is an error: Certo
  never uses an inactive model. Set `activated: true` on it to benchmark
  it. (Before version 0.1.9 the flag was ignored here.)
- Problems in `models.yaml` are checked as for every command (see
  [models.yaml](models-yaml.md#checks)): errors stop the benchmark,
  warnings are printed with the plan.
- `task_profiles` in `models.yaml` are not used.

## Strategies to come

Strategies are a small registry in Certo's code, so new ones can be added
without changing how the benchmark runs, for example `cascade` (several
models in order) or `best_of` (several attempts, the verifier picks).
Only `single` exists today.
