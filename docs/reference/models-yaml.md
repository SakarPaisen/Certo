# models.yaml and models_list.yaml

The format of the two files behind automatic model selection
(`--auto-model`), escalation (`--escalate`) and the benchmark
(`certo bench`). It is for looking things up; the guides are
[Pick models automatically](../guides/pick-models-automatically.md),
[Escalate between models](../guides/escalate-between-models.md) and
[Benchmark models and strategies](../guides/benchmark.md).

- **`models_list.yaml`** is the catalog: which models exist, their LiteLLM
  ids, descriptions and ratings, the task profiles and the escalation
  ladders. It holds no keys and no addresses.
- **`models.yaml`** holds your personal settings: which models of the list
  you use, each with its API key or server address, whether it is
  activated, and any overrides. It holds keys: keep it out of git.

Certo needs both. It reads them for `--auto-model` and `--escalate` (or
`CERTO_MODEL_SELECTION=auto` / `escalate`), for `certo check` and for
`certo bench`. With the default (manual) selection, neither is read.

## Start from the examples

Certo ships both files only as examples, inside the package, and never
reads an example. Copy each one and edit your copy:

```bash
cp <examples>/models_list.yaml.example ~/.config/certo/models_list.yaml
cp <examples>/models.yaml.example ~/.config/certo/models.yaml
```

`certo check` prints the exact `cp` command, with the examples folder of
your installation, when a file is missing. In the repository the examples
are [models_list.yaml.example](../../src/certo/examples/models_list.yaml.example)
and [models.yaml.example](../../src/certo/examples/models.yaml.example). A
new Certo release can update the examples; it never touches your copies,
so add models and change ratings in your copy freely.

## Where Certo looks

Each file is looked up on its own, in this order, and the first one found
is used whole:

1. the path a setting names: `CERTO_MODELS_LIST_FILE` and
   `CERTO_MODELS_FILE` (for `certo bench`: `models_list_file` and
   `models_file` in its benchmark file);
2. the current folder (the project folder): `./models_list.yaml`,
   `./models.yaml`;
3. the user settings folder, next to the user `.env`:
   `~/.config/certo/` (or `$XDG_CONFIG_HOME/certo/`).

So files in a project folder override the ones in your user settings
folder. A setting that names a file that doesn't exist is an error.

## `models_list.yaml`

```yaml
models:          # required, a non-empty list
  - name: qwen3-coder-local
    model: ollama/qwen3-coder:30b
    timeout_seconds: 900
    description: ...
    ratings: {reasoning: 1, precision: 2, code: 1, cost: 5}

task_profiles:   # optional
  debugging:
    triggers: [...]
    weights: {...}
  default:
    weights: {...}

escalation:      # optional
  cost_axis: cost
  max_rungs: 3
  ladders:
    default:
      - model: ...
```

| Model field | Required | Meaning |
|---|---|---|
| `name` | yes | A short, unique name. `models.yaml` and ladders refer to the model by it. Used in logs, in the `Model used:` line and in `MODEL_DECISIONS.md`. |
| `model` | yes | The LiteLLM model id, as in `CERTO_LLM_MODEL`. |
| `reasoning_effort` | no | As `CERTO_LLM_REASONING_EFFORT`. Empty means the default. |
| `timeout_seconds` | no | As `CERTO_LLM_TIMEOUT_SECONDS`: how long one call to this model may take, a whole number of seconds. Default `300`; `0` means no limit. |
| `description` | no | Shown when `--interactive` asks you to pick a model. |
| `ratings` | no | A map of axis name to number, usually 1 to 5. |

`api_key`, `base_url` and `activated` are not allowed here: they are
personal and go in `models.yaml`.

## `models.yaml`

```yaml
models:          # required, a non-empty list
  - name: qwen3-coder-local          # a name from models_list.yaml
    base_url: http://localhost:11434
  - name: gpt-6-luna
    api_key: sk-...
  - name: claude-sonnet-5-5
    api_key: sk-...
    activated: false
    ratings: {code: 4}               # an override
```

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | The `name` of a model in `models_list.yaml`. A name the list doesn't have is an error: add new models to the list. |
| `api_key` | no | As `CERTO_LLM_API_KEY`. Empty means no key. |
| `base_url` | no | As `CERTO_LLM_BASE_URL`, for Ollama and other local or self-hosted servers. Empty means the provider's default. |
| `activated` | no | `true` (default) or `false`. A `false` entry stays in the file but is never used. |
| `ratings` | no | Overrides, axis by axis: `{code: 4}` changes only `code`; the other axes keep the list's values. |
| `reasoning_effort`, `timeout_seconds`, `description` | no | Overrides of the list's values. |

**Only the models listed here, and not `activated: false`, are ever
used**: not in `--auto-model`, not in an escalation ladder, and not in
`certo bench`. A model that is only in `models_list.yaml` is known (ladders
may name it) but skipped.

Each model is complete on its own: settings it leaves empty are **not**
taken from `CERTO_LLM_*`. A local model with no `api_key` never gets the
key of another provider. `CERTO_LLM_MODEL` must still be set, because
Certo checks the normal settings first.

Before version 0.1.10 everything was in `models.yaml`. An old-style file
(with model ids, `task_profiles` or `escalation`) is an error that says
what to move to `models_list.yaml`.

## Ratings: higher is always better

The axis names are yours. The example list uses `reasoning`, `precision`,
`code` and `cost`, but you can add any name, such as `latency`.

On every axis, a higher number must mean "more of what I want". For `cost`
this means **cost-effectiveness**: `cost: 5` is a cheap (or free, local)
model, `cost: 1` an expensive one. The example list explains the scale
behind its numbers in its comments.

## `task_profiles`

A profile says which axes matter for a kind of task, for `--auto-model`.

| Field | Meaning |
|---|---|
| `triggers` | A list of words or phrases. A profile matches when one of them appears in the task's first line with text (a task file's title, or the whole task when it is one line), as a whole word or with a plural `s`/`es`, in any case. |
| `weights` | A map of axis name to number. |
| `model` | Optional. The name of a model in `models_list.yaml` to run first for this profile, whatever the weights say. Used only when that model is enabled in `models.yaml`; otherwise the weights decide, and `MODEL_DECISIONS.md` says why. The weights still order the fallbacks after it. A name that isn't in `models_list.yaml` is an error in `certo check`; a model that isn't enabled is a warning. |

**Choosing the profile.** The profiles are tried in the order of the file,
skipping the one named `default`. The first that matches wins. If none
matches, the `default` profile is used. Put specific profiles before broad
ones.

**Scoring.** For each active model:

```text
score = sum of rating[axis] × weight[axis], over the profile's weights
```

An axis the model doesn't rate counts as 0. Models are ranked by score,
highest first; equal scores keep the order of the list. If no profile
matches and there is no `default`, every model scores 0 and the order of
the list decides.

## `escalation`

Settings for escalation: running a task on the first model of a ladder,
and moving to the next one only when Certo's verification shows the model
couldn't finish, or its provider fails. The whole section is optional. The guide, with how a
derived ladder is computed, is
[Escalate between models](../guides/escalate-between-models.md).

| Field | Default | Meaning |
|---|---|---|
| `cost_axis` | `cost` | The rating axis that means cost-effectiveness. A model's capability, for escalation, is the sum of its ratings on every other axis (usually `reasoning + precision + code`). A derived ladder uses the cost axis to start from the cheapest models and to leave out a model that another one beats at the same price or less. |
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
| `reasoning_effort` | no | Reasoning effort for this rung only, instead of the model's own. |

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
With no ladder at all, Certo builds one from the enabled models' ratings.
A rung whose model isn't enabled in `models.yaml` is skipped.

## Checks

Every command that reads the files checks them the same way. Errors stop
the command; warnings are printed, and the command runs.

Errors:

- a file is missing or not valid YAML, `models` is missing or empty, an
  entry has no `name` (or, in the list, no `model`), a rating or weight is
  not a number, or a field has the wrong type or an unknown name;
- `models_list.yaml` has an `api_key`, `base_url` or `activated`;
- `models.yaml` is in the old single-file format;
- two models in the list share a name, or `models.yaml` lists one twice;
- `models.yaml` names a model the list doesn't have;
- no model is enabled (none listed in `models.yaml`, or all
  `activated: false`);
- a ladder rung names a model that doesn't exist (the message lists the
  names that do);
- a ladder lists the same model twice with the same settings (the same
  model with a different `reasoning_effort` is allowed);
- a rung has a negative `retries`;
- `escalation.cost_axis` is set, and no model has a rating with that name;
- a ladder has no usable rung.

Warnings:

- a rung names a model that isn't in `models.yaml`, or has
  `activated: false`: the rung is skipped;
- a ladder has a single usable rung, so it can't escalate;
- an enabled model has no rating on an axis that a task profile weighs: it
  counts as 0;
- an enabled model has no `api_key` and no `base_url`: it works only if
  the provider's own key variable (such as `OPENAI_API_KEY`) is set;
- a ladder goes from a more capable model to a less capable one
  (capability: the sum of the ratings except the cost axis). Allowed,
  since you may know better, but check the order.
