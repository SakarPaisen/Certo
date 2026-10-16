# models.yaml

The format of the model list used by automatic model selection
(`--auto-model`) and by the benchmark (`certo bench`). It is for looking
things up; the guides are
[Pick models automatically](../guides/pick-models-automatically.md) and
[Benchmark models and strategies](../guides/benchmark.md). The benchmark
uses only `models` entries, by name, and ignores `activated` and
`task_profiles`.

Certo reads the file only for `--auto-model` (or
`CERTO_MODEL_SELECTION=auto`) and for `certo bench`. For `--auto-model`
its path is `./models.yaml`, or `CERTO_MODELS_FILE`; `certo bench` uses
the `models_file` of its benchmark file (default `./models.yaml`) and
doesn't read `CERTO_MODELS_FILE`. It holds API keys: keep it out of git. A full example
with many providers is [models.yaml.example](../../models.yaml.example) in
the repository.

## Layout

```yaml
models:          # required, a non-empty list
  - name: ...
    model: ...
    # more fields below

task_profiles:   # optional
  debugging:
    triggers: [...]
    weights: {...}
  default:
    weights: {...}
```

## `models` entries

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | A short, unique name. Used in logs, in the `Model used:` line and in `MODEL_DECISIONS.md`. Two entries with the same name are an error. |
| `model` | yes | The LiteLLM model id, as in `CERTO_LLM_MODEL`. |
| `api_key` | no | As `CERTO_LLM_API_KEY`. Empty means no key. |
| `base_url` | no | As `CERTO_LLM_BASE_URL`. Empty means the provider's default. |
| `reasoning_effort` | no | As `CERTO_LLM_REASONING_EFFORT`. Empty means the default. |
| `timeout_seconds` | no | As `CERTO_LLM_TIMEOUT_SECONDS`: how long one call to this model may take, a whole number of seconds. Default `300`; `0` means no limit. |
| `description` | no | Shown when `--interactive` asks you to pick a model. |
| `ratings` | no | A map of axis name to number, usually 0 to 5. |
| `activated` | no | `true` (default) or `false`. A `false` entry is still checked for errors, but never scored, chosen or used as a fallback. |

Each entry is complete on its own: settings it leaves empty are **not**
taken from `CERTO_LLM_*`. A local model with no `api_key` never gets the
key of another provider.

`CERTO_LLM_MODEL` must still be set, because Certo checks the normal
settings before it reads this file.

## Ratings: higher is always better

The axis names are yours. The example file uses `reasoning`, `cost`,
`precision` and `code`, but you can add any name, such as `latency`.

On every axis, a higher number must mean "more of what I want". For `cost`
this means **cost-effectiveness**: `cost: 5` is a cheap model, `cost: 1` an
expensive one.

## `task_profiles`

A profile says which axes matter for a kind of task.

| Field | Meaning |
|---|---|
| `triggers` | A list of words or phrases. A profile matches when one of them appears anywhere in the task text (any case, also inside a longer word). |
| `weights` | A map of axis name to number. |

**Choosing the profile.** The profiles are tried in the order of the file,
skipping the one named `default`. The first that matches wins. If none
matches, the `default` profile is used. Put specific profiles before broad
ones.

**Scoring.** For each active model:

```text
score = sum of rating[axis] × weight[axis], over the profile's weights
```

An axis the model doesn't rate counts as 0. Models are ranked by score,
highest first; equal scores keep the order of the file. If no profile
matches and there is no `default`, every model scores 0 and the order of
the file decides.

## Errors

Certo stops with a clear message if the file is missing or not valid
YAML, if `models` is missing or empty, if an entry has no `name` or
`model`, if a rating or weight is not a number, if two entries share a
name, or if every entry has `activated: false`.
