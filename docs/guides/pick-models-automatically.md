# Pick models automatically

This guide shows how to give Certo a list of models and let it choose the
best one for each task, with fallback to the next model when one fails. It
is for people who use several models and want cheap models on simple tasks
and strong models on hard ones.

The choice uses simple keyword rules and scores you write. It makes no
extra model call.

## 1. Create `models_list.yaml` and `models.yaml`

Certo uses two files, and ships both only as examples:

- **`models_list.yaml`**, the catalog: the models, their ratings and the
  task profiles. No keys.
- **`models.yaml`**, your personal settings: the models you use, by name,
  each with its key or server address. It holds keys: keep it out of git,
  like `.env`.

Copy both examples into your user settings folder (or into a project
folder, which then overrides them). `certo check` prints the exact
commands for your installation when a file is missing:

```bash
cp <examples>/models_list.yaml.example ~/.config/certo/models_list.yaml
cp <examples>/models.yaml.example ~/.config/certo/models.yaml
```

The list describes the models. A short one:

```yaml
# models_list.yaml
models:
  - name: claude-sonnet
    model: anthropic/claude-sonnet-5-5
    description: "Strong, well-rounded coding model."
    ratings: {reasoning: 4, precision: 4, code: 5, cost: 2}

  - name: local-coder
    model: ollama/qwen3-coder:30b
    description: "Free, local, weaker on hard tasks."
    ratings: {reasoning: 1, precision: 2, code: 1, cost: 5}

task_profiles:
  debugging:
    triggers: [fix, bug, crash, "failing test"]
    weights: {reasoning: 3, precision: 2, code: 2, cost: 0.5}
  default:
    weights: {reasoning: 1, cost: 1, precision: 1, code: 1}
```

`models.yaml` picks the ones you use and adds what's personal:

```yaml
# models.yaml
models:
  - name: claude-sonnet
    api_key: "sk-ant-..."
  - name: local-coder
    base_url: "http://localhost:11434"
```

- Only the models listed in `models.yaml` are used. `activated: false`
  keeps an entry there without using it.
- To add a model, add it to `models_list.yaml` first, then name it in
  `models.yaml`. To change a rating for yourself only, override it in
  `models.yaml` (`ratings: {code: 4}`).
- Run `certo check` to see what Certo makes of the files: the active
  models and every error or warning. `certo check --models` also tests
  each active model with a real request.
- On every rating, **higher is better, including `cost`**: `cost: 5` means
  cheap.

Every field is in the [reference](../reference/models-yaml.md).

## 2. Run with `--auto-model`

```bash
certo "Fix the failing test in payments.py" --auto-model
```

Or set `CERTO_MODEL_SELECTION=auto` in your settings. Where Certo finds
the two files is in the [reference](../reference/models-yaml.md#where-certo-looks).

`CERTO_LLM_MODEL` must still be set: Certo checks the normal settings
before it reads the model files. Problems in them are reported the same
way for every command: errors stop the run, warnings are printed (see
[Checks](../reference/models-yaml.md#checks)).

## How a model is chosen

1. **Classify the task.** Certo looks for each profile's `triggers` in the
   task text (ignoring case). The first profile in the file that matches
   wins. If none matches, it uses the profile named `default`.
2. **Score every active model.** The score is the sum of
   `rating × weight` over the profile's weights.
3. **Run the best one.** Models are ranked by score, once, at the start.
   Ties keep the order of the file.
4. **Fall back when needed.** Certo moves to the next model in the ranking
   when the current one:
   - fails at the provider (bad key, rate limit, outage, context too long),
     or
   - makes a fix attempt that still fails Certo's checks.

When every model has been tried, the task ends as it would without
automatic selection.

With `--interactive` as well, Certo shows the ranked list and asks which
model to use, with the best one as the default.

## See what was chosen and why

Before the verdict, the output says which model did the work:

```text
Model used: claude-sonnet (see MODEL_DECISIONS.md for the full history)
```

`MODEL_DECISIONS.md` in the project folder records every decision, even
when the task failed. For the task and file above:

```markdown
# Model Decisions

## initial — 2026-10-16T06:18:18.190751+00:00

Reason: Task classified as 'debugging' (weights: {'reasoning': 3.0, 'precision': 2.0, 'code': 2.0, 'cost': 0.5}).

Task profile: `debugging` (weights: {'reasoning': 3.0, 'precision': 2.0, 'code': 2.0, 'cost': 0.5})

Ranked candidates:
- **claude-sonnet** (score 31.50)
- local-coder (score 25.50)

Chosen: **claude-sonnet**
```

Each fallback adds a section of its own, with the reason for the switch.

## Limits

- The ranking is computed once per task. Falling back moves to the next
  best fit for this kind of task, which is not always a stronger model.
- Under `--execution docker`, the first choice works, but Certo can't
  switch models in the middle of a task.

## Automatic choice or escalation?

`--auto-model` picks the best fit for each task up front and switches only
on errors or failed fix attempts, inside one conversation. To start cheap
and pay for a stronger model only when the cheap one's work fails
verification, use [escalation](escalate-between-models.md) instead:
`--escalate`. The two can't be combined. How they differ, with use cases:
[Auto-model or escalation](../concepts/auto-model-or-escalation.md).

## Related

- [models.yaml and models_list.yaml](../reference/models-yaml.md)
- [Escalate between models](escalate-between-models.md)
- [Run records and costs](run-records-and-costs.md): tokens and cost per model
