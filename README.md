# Certo

**The coding agent that doesn't take its own word for it.**

[![PyPI](https://img.shields.io/pypi/v/certo.svg)](https://pypi.org/project/certo/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/alessioricco/certo/blob/main/LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://github.com/alessioricco/certo/blob/main/pyproject.toml)
[![Built on OpenHands SDK](https://img.shields.io/badge/built%20on-OpenHands%20SDK-6f42c1.svg)](https://docs.openhands.dev/sdk)

Give Certo a task. An agent plans, edits files and runs commands until it says it's done. Then Certo re-runs your project's real tests and build itself, with no LLM involved, and tells you whether the work is actually verified. Any model, local or cloud. *Certo* is Italian for "sure".


## Why

Coding agents are confident, and often wrong about being finished. One example from building this tool: an agent wrote a Tower of Hanoi game, every unit test passed, and the program crashed the moment a user picked "solve". The agent had reported success, and so had pytest.

Certo exists to catch that. When the agent finishes, the harness checks the result independently, sends real failures back for another attempt, and stops when a fix attempt changes nothing.

## Quickstart

```bash
pip install certo
certo init
cd certo-workspace
certo tasks/wordle.md --project wordle
```

`certo init` asks which provider you use (OpenAI, Anthropic, Gemini, a local Ollama, or any LiteLLM model), takes your API key at a hidden prompt, saves the settings, and makes one real call to check the model works. It also leaves two sample tasks in `tasks/`: a terminal Wordle in Python and a browser Asteroids game (which needs Node 18+). With a cloud model a run uses your credits, and Certo prints the cost at the end.

Or work on one project at a time, new or existing:

```bash
cd any-project && certo "Add a --verbose flag, with a test"
```

This works in any folder when `certo init` saved your settings for "all projects on this computer", its default.

The generated project lands in `projects/wordle`. The last line of output is the verdict:

```
Verification: verified
```

`certo check` shows where each setting comes from and re-runs the model check. Before the agent edits a folder that already has files, Certo prints a one-line warning if it has uncommitted git changes, or isn't a git repository.

### Without `certo init`

Set two variables instead, in your shell, in a `.env` in the folder you run `certo` from, or in `~/.config/certo/.env` for every folder ([details](https://github.com/alessioricco/certo/blob/main/docs/reference/configuration.md#where-certo-looks)):

```bash
export CERTO_LLM_MODEL=anthropic/claude-sonnet-5-5   # or openai/..., gemini/..., deepseek/...
export CERTO_LLM_API_KEY=sk-...

certo "Build a CLI todo app in Python, with tests" --project todo
```

With a local model (no API key):

```bash
ollama pull qwen3-coder:30b
export CERTO_LLM_MODEL=ollama/qwen3-coder:30b
export CERTO_LLM_BASE_URL=http://localhost:11434
```

`qwen3-coder:30b` needs roughly 20 GB of GPU or unified memory. With less, pull a smaller coder model such as `qwen2.5-coder:7b` and set `CERTO_LLM_MODEL=ollama/qwen2.5-coder:7b`. Expect weaker results on multi-step tasks.

## What the verdict means

| State | Meaning |
| --- | --- |
| `verified` | The project's own tests or build ran and passed. |
| `inconclusive` | Nothing could be checked (no tests yet, unknown project type, missing toolchain). |
| `retry_exhausted` | A check kept failing after the automatic fix attempts. |
| `no_progress` | A fix attempt changed nothing in the failing output, so Certo stopped early. |
| `incomplete` | The agent left items on its own to-do list unfinished. |
| `budget_exhausted` | The task ran out of its time budget. |

The exit code is nonzero for every failure state, so Certo works in scripts and CI. Add `--require-verification` to make `inconclusive` fail too. Every state and its exit code: [Verdicts](https://github.com/alessioricco/certo/blob/main/docs/reference/verdicts.md).

## Features

- **Independent verification.** Re-runs the project's real test, build, lint and typecheck commands after the agent finishes. It never invents a command the project doesn't configure.
- **Works across languages.** Detects and verifies Python, Node/JS/TS, Go, Rust and Java (Maven/Gradle) projects. Each Python project gets its own virtual environment, used by both the agent and the checks.
- **Verify without an agent.** `certo verify [PATH]` runs the same checks on any project, with no model needed.
- **Any model, one setting.** Ollama, Anthropic, OpenAI, Gemini, DeepSeek or Moonshot. Switching is one environment variable.
- **Picks the best model per task.** Rate your models in `models_list.yaml`, enable the ones you have keys for in `models.yaml`, and Certo routes each task to the best fit, with fallback when a provider fails. No extra LLM call to decide. Add `--auto-model`.
- **Hard limits.** An iteration cap, a wall-clock budget across all retries, and an optional approve-every-action mode.
- **Sandboxed runs.** Add `--execution docker` to run the agent in a container.
- **Server mode.** REST, WebSocket streaming, and an OpenAI-compatible `/v1/chat/completions` endpoint.
- **Run records.** Full transcript, token counts and cost per run, plus a log of which model was picked and why.
- **Escalates only when it must.** Give Certo a ladder of models from `models_list.yaml`, cheapest first. Each task starts on the first; it moves to the next, stronger model only when Certo's verification shows the cheaper one couldn't finish. Per task, not per step. Add `--escalate`. See [Escalate between models](https://github.com/alessioricco/certo/blob/main/docs/guides/escalate-between-models.md).
- **A benchmark.** `certo bench` compares models on bundled tasks graded by hidden tests the agent never sees, and counts how often Certo itself was fooled. See [Benchmark models and strategies](https://github.com/alessioricco/certo/blob/main/docs/guides/benchmark.md).
- **Skills and custom tools.** Add project conventions or new tools by dropping files in a folder.

## More ways to run it

```bash
# Work inside a sandbox
certo "Add a /version endpoint" --project my-api --execution docker

# Let Certo choose the model for the task
certo "Fix the failing test in payments.py" --project my-api --auto-model

# Take the task from a file or URL
certo ./tasks/spec.md --project my-api

# Pause and ask you questions instead of guessing
certo "Scaffold a FastAPI service" --project my-api --interactive

# Check a project with Certo's verification only: no agent, no model
certo verify ./projects/my-api
```

## How it works

Certo is built on the [OpenHands Software Agent SDK](https://docs.openhands.dev/sdk), which runs the agent loop and tools. Certo adds the parts the SDK leaves open: what counts as verified, which model runs and when to fall back, the budgets, and the CLI and server you talk to.

## Known limits

- Server mode has no authentication. Run it on localhost or behind your own gateway.
- Java projects are detected, but verification needs Maven or Gradle installed.
- Under Docker, automatic model selection makes the initial pick but does not fall back mid-task.
- Small local models can struggle with multi-step tool use. A coder-tuned model gives the best results.

The full list is in the [documentation](https://github.com/alessioricco/certo/blob/main/docs/README.md#known-limitations).

## Documentation

- [Documentation home](https://github.com/alessioricco/certo/blob/main/docs/README.md): guides, reference and concepts, organised by what you want to do
- [Getting started](https://github.com/alessioricco/certo/blob/main/docs/getting-started.md): install, `certo init`, your first task, and reading the verdict
- [Troubleshooting](https://github.com/alessioricco/certo/blob/main/docs/troubleshooting.md): the problems people actually hit, with their fix
- [Why agents lie](https://github.com/alessioricco/certo/blob/main/docs/concepts/why-agents-lie.md): the real cases of agents claiming "done", and how Certo catches each one
- [ROADMAP.md](https://github.com/alessioricco/certo/blob/main/ROADMAP.md): status, backlog, and design decisions

## Contributing

Issues and pull requests are welcome. Issues labelled [good first issue](https://github.com/alessioricco/certo/labels/good%20first%20issue) are a good place to start. To work on the code:

```bash
git clone https://github.com/alessioricco/certo.git
cd certo
uv pip install -e ".[dev]"
uv run pytest -q     # no API key needed
```

## License

[MIT](https://github.com/alessioricco/certo/blob/main/LICENSE). Built by [Alessio Ricco](https://github.com/alessioricco).