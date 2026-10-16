# Pick models automatically

This guide shows how to give Certo a list of models and let it choose the
best one for each task, with fallback to the next model when one fails. It
is for people who use several models and want cheap models on simple tasks
and strong models on hard ones.

The choice uses simple keyword rules and scores you write. It makes no
extra model call.

## 1. Write `models.yaml`

Start from the example in the repository,
[models.yaml.example](../../models.yaml.example), and save it as
`models.yaml` in the folder where you run `certo`. A small one:

```yaml
models:
  - name: claude-sonnet
    model: anthropic/claude-sonnet-5-5
    api_key: "sk-ant-..."
    description: "Strong, well-rounded coding model."
    ratings: {reasoning: 4, cost: 3, precision: 4, code: 5}
    activated: true

  - name: local-coder
    model: ollama/qwen3-coder:30b
    base_url: "http://localhost:11434"
    description: "Free, local, weaker on hard tasks."
    ratings: {reasoning: 3, cost: 5, precision: 3, code: 4}
    activated: true

task_profiles:
  debugging:
    triggers: [fix, bug, crash, "failing test"]
    weights: {reasoning: 3, precision: 2, code: 2, cost: 0.5}
  default:
    weights: {reasoning: 1, cost: 1, precision: 1, code: 1}
```

- `models.yaml` holds real API keys. Keep it out of git, like `.env`.
- Every model in the example file starts with `activated: false`. Turn on
  only the ones whose keys you filled in.
- On every rating, **higher is better, including `cost`**: `cost: 5` means
  cheap.

Every field is in the [models.yaml reference](../reference/models-yaml.md).

## 2. Run with `--auto-model`

```bash
certo "Fix the failing test in payments.py" --auto-model
```

Or set `CERTO_MODEL_SELECTION=auto` in your settings. Certo reads
`./models.yaml`, or the file named by `CERTO_MODELS_FILE`.

`CERTO_LLM_MODEL` must still be set: Certo checks the normal settings
before it reads the model list.

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

## Related

- [models.yaml reference](../reference/models-yaml.md)
- [Run records and costs](run-records-and-costs.md): tokens and cost per model
