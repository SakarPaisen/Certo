# models.yaml

The format of the model list used by automatic model selection
(`--auto-model`) and by the benchmark (`certo bench`). It is for looking
things up; the guides are
[Pick models automatically](../guides/pick-models-automatically.md) and
[Benchmark models and strategies](../guides/benchmark.md). The benchmark
uses `models` entries by name, and ignores `task_profiles`.

**`activated: false` means Certo never uses that model**, in every
command: not in `--auto-model`, not in an escalation ladder, and not in
`certo bench`.

Certo reads the file for `--auto-model` and `--escalate` (or
`CERTO_MODEL_SELECTION=auto` / `escalate`), for `certo check`, and for
`certo bench`. Its path is `./models.yaml`, or `CERTO_MODELS_FILE`;
`certo bench` uses the `models_file` of its benchmark file (default
`./models.yaml`) and doesn't read `CERTO_MODELS_FILE`. It holds API keys: keep it out of git. A full example
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

escalation:      # optional, for escalation between models
  cost_axis: cost
  max_rungs: 3
  ladders:
    default:
      - model: ...
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

## `escalation`

Settings for escalation: running a task on a cheap model first, and moving
to a stronger one only when Certo's verification shows the cheap one
couldn't finish. The whole section is optional. The guide, with how a
derived ladder is computed, is
[Escalate between models](../guides/escalate-between-models.md).

| Field | Default | Meaning |
|---|---|---|
| `cost_axis` | `cost` | The rating axis that means cost-effectiveness. A model's capability, for escalation, is the sum of its ratings on every other axis (usually `reasoning + precision + code`); the cost axis only breaks ties. |
| `max_rungs` | `3` | The longest ladder Certo builds from the ratings. A whole number, at least 2. |
| `ladders` | none | Ladders you write yourself, by name. |

**A ladder** is a list of rungs, tried in order:

```yaml
escalation:
  ladders:
    default:
      - model: qwen-local      # a name from models:
        retries: 1             # optional
        reasoning_effort: ""   # optional
      - model: gpt-luna
      - model: claude-sonnet
```

| Rung field | Required | Meaning |
|---|---|---|
| `model` | yes | The `name` of a model in `models`. |
| `retries` | no | Fix attempts on this rung after a failed check. Default: `CERTO_MAX_VERIFY_RETRIES`. |
| `reasoning_effort` | no | Reasoning effort for this rung only, instead of the model entry's own. |

To set an option for a ladder, write it as a mapping with its rungs under
`rungs`:

```yaml
    local-only:
      escalate_on_acceptance_failed: true
      rungs:
        - model: qwen-local
        - model: gemma-local
          reasoning_effort: max
```

`escalate_on_acceptance_failed` (default `false`) also moves to the next
rung when a required acceptance check fails.

A ladder named `default` is the one used when no ladder name is given.
With no ladder at all, Certo builds one from the active models' ratings.

## Checks

Every command that reads the file checks it the same way. Errors stop the
command; warnings are printed, and the command runs.

Errors:

- the file is missing or not valid YAML, `models` is missing or empty, an
  entry has no `name` or `model`, a rating or weight is not a number, or a
  field has the wrong type;
- two models share a name;
- every model has `activated: false`;
- a ladder rung names a model that doesn't exist (the message lists the
  names that do);
- a ladder lists the same model twice with the same settings (the same
  model with a different `reasoning_effort` is allowed);
- a rung has a negative `retries`;
- `escalation.cost_axis` is set, and no model has a rating with that name;
- a ladder has no usable rung once inactive models are removed.

Warnings:

- a rung names a model with `activated: false`: the rung is skipped;
- a ladder has a single usable rung, so it can't escalate;
- an active model has no rating on an axis that a task profile weighs: it
  counts as 0;
- an active model has no `api_key` and no `base_url`: it works only if the
  provider's own key variable (such as `OPENAI_API_KEY`) is set;
- a ladder goes from a more capable model to a less capable one
  (capability: the sum of the ratings except the cost axis). Allowed,
  since you may know better, but check the order.
