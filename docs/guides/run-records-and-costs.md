# Run records and costs

This guide explains the summary Certo prints after every run, and how to
keep a full record of each run on disk: the transcript, the tokens and the
cost.

## The run summary

Every `certo` run ends with a summary after the verdict:

```text
Run summary:
  Total running time: 4m 03s
  Models: openai/gpt-5.6-luna
  Total tokens: 801,191 (input 774,063, of which cached 725,104; output 27,128)
  Total cost: $0.0593
```

- **Total running time** covers the whole task: every agent run, Certo's
  checks and retries, and any time waiting for your answers.
- **Models** lists every model that made calls. With
  [automatic model selection](pick-models-automatically.md), a fallback
  adds a second model, and one line per model with its tokens and cost.
- **Total tokens** is input plus output. Cached input is part of the input
  number.
- **Total cost** uses LiteLLM's prices. When LiteLLM has no price for a
  model (common for local models), the line ends with
  `+ unknown (no pricing data for ...)`. That means unknown, not free.

## Keep a record of every run

Set `CERTO_ARTIFACTS_DIR` to a folder:

```bash
CERTO_ARTIFACTS_DIR=./artifacts certo "Add a /version endpoint" --project my-api
```

Each run gets its own folder:

```text
artifacts/
  my-api/              the --project name, or _unscoped without one
    <run-id>/
      metadata.json
      transcript.json
      metrics.json
```

The folder sits next to your projects, not inside them, so it never ends up
in a project's git history. Runs are never overwritten. In server mode,
`POST /tasks` runs use the task id as the run id.

| File | What it holds |
|---|---|
| `metadata.json` | The task, project, model, execution mode, start and end time, verdict, what was checked and any limitations, acceptance results, the run summary, and the error if the run failed. Written even when the run fails. |
| `transcript.json` | Every message of the run. |
| `metrics.json` | Tokens and cost: `summary` (same as above), `combined`, and `per_model`. |

## Model decisions

With automatic model selection, `MODEL_DECISIONS.md` in the project folder
records which model was chosen and why. It is written whether or not
`CERTO_ARTIFACTS_DIR` is set. See
[Pick models automatically](pick-models-automatically.md).

## Related

- [Configuration](../reference/configuration.md)
- [OpenAI, Claude and Gemini](openai-claude-gemini.md#cost)
