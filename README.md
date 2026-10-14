# Certo

**The coding agent that doesn't take its own word for it.**

[![PyPI](https://img.shields.io/pypi/v/certo.svg)](https://pypi.org/project/certo/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![Built on OpenHands SDK](https://img.shields.io/badge/built%20on-OpenHands%20SDK-6f42c1.svg)](https://docs.openhands.dev/sdk)

Give Certo a task. An agent plans, edits files and runs commands until it says it's done. Then Certo re-runs your project's real tests and build itself, with no LLM involved, and tells you whether the work is actually verified. Any model, local or cloud. *Certo* is Italian for "sure".


## Why

Coding agents are confident, and often wrong about being finished. One example from building this tool: an agent wrote a Tower of Hanoi game, every unit test passed, and the program crashed the moment a user picked "solve". The agent had reported success, and so had pytest.

Certo exists to catch that. When the agent finishes, the harness checks the result independently, sends real failures back for another attempt, and stops when a fix attempt changes nothing.

## Quickstart

With a local model (no API key):

```bash
pip install certo
ollama pull qwen2.5-coder

export LLM_MODEL=ollama/qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434

certo "Build a CLI todo app in Python, with tests" --project todo
```

With a cloud model, change two lines:

```bash
export LLM_MODEL=anthropic/claude-sonnet-4-5-20250929   # or openai/..., gemini/..., deepseek/...
export LLM_API_KEY=sk-...
```

The generated project lands in `./projects/todo`. The last line of output is the verdict:

```
Verification: verified
```

## What the verdict means

| State | Meaning |
| --- | --- |
| `verified` | The project's own tests or build ran and passed. |
| `inconclusive` | Nothing could be checked (no tests yet, unknown project type, missing toolchain). |
| `retry_exhausted` | A check kept failing after the automatic fix attempts. |
| `no_progress` | A fix attempt changed nothing in the failing output, so Certo stopped early. |
| `incomplete` | The agent left items on its own to-do list unfinished. |
| `budget_exhausted` | The task ran out of its time budget. |

The exit code is nonzero for every failure state, so Certo works in scripts and CI. Add `--require-verification` to make `inconclusive` fail too. The full list of states is in the [manual](MANUAL.md#test-verification).

## Features

- **Independent verification.** Re-runs the project's real test, build, lint and typecheck commands after the agent finishes. It never invents a command the project doesn't configure.
- **Works across languages.** Detects and verifies Python, Node/JS/TS, Go, Rust and Java (Maven/Gradle) projects.
- **Any model, one setting.** Ollama, Anthropic, OpenAI, Gemini, DeepSeek or Moonshot. Switching is one environment variable.
- **Picks the best model per task.** List your models with cost and quality ratings in `models.yaml` and Certo routes each task to the best fit, with fallback when a provider fails. No extra LLM call to decide. Add `--auto-model`.
- **Hard limits.** An iteration cap, a wall-clock budget across all retries, and an optional approve-every-action mode.
- **Sandboxed runs.** Add `--execution docker` to run the agent in a container.
- **Server mode.** REST, WebSocket streaming, and an OpenAI-compatible `/v1/chat/completions` endpoint.
- **Run records.** Full transcript, token counts and cost per run, plus a log of which model was picked and why.
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
```

## How it works

Certo is built on the [OpenHands Software Agent SDK](https://docs.openhands.dev/sdk), which runs the agent loop and tools. Certo adds the parts the SDK leaves open: what counts as verified, which model runs and when to fall back, the budgets, and the CLI and server you talk to.

## Known limits

- Server mode has no authentication. Run it on localhost or behind your own gateway.
- Java projects are detected, but verification needs Maven or Gradle installed.
- Under Docker, automatic model selection makes the initial pick but does not fall back mid-task.
- Small local models can struggle with multi-step tool use. A coder-tuned model gives the best results.

The full list is in the [manual](MANUAL.md#known-limitations).

## Documentation

- [MANUAL.md](MANUAL.md): configuration, CLI flags, server API, skills, custom tools
- [ROADMAP.md](ROADMAP.md): status, backlog, and the log of every agent failure that shaped the design

## Contributing

Issues and pull requests are welcome. Issues labelled [good first issue](https://github.com/alessioricco/certo/labels/good%20first%20issue) are a good place to start. To work on the code:

```bash
git clone https://github.com/alessioricco/certo.git
cd certo
uv pip install -e ".[dev]"
uv run pytest -q     # no API key needed
```

## License

[MIT](LICENSE). Built by [Alessio Ricco](https://github.com/alessioricco).