# Certo v0.1.0

Certo is a model-agnostic coding agent built on the OpenHands Software Agent
SDK: give it a task and an agent plans, edits files and runs commands until
it says it's done. Then Certo re-runs your project's real tests and build
itself, with no LLM involved, and tells you whether the work is actually
verified.

This is the first release on PyPI. It is alpha software.

## Main features

- **Independent verification.** After the agent finishes, Certo re-runs the
  project's own test, build, lint and typecheck commands and reports one
  verdict: `verified`, `inconclusive`, `retry_exhausted`, `no_progress`,
  `incomplete` or `budget_exhausted`. Real failures go back to the agent for
  another attempt, and Certo stops early when a fix attempt changes nothing.
  It never invents a command the project doesn't configure.
- **Works across languages.** Detects and verifies Python, Node/JS/TS, Go,
  Rust and Java (Maven/Gradle) projects.
- **Any model, one setting.** Ollama, Anthropic, OpenAI, Gemini, DeepSeek or
  Moonshot via `LLM_MODEL`. Switching provider is one environment variable.
- **Picks the best model per task.** With `--auto-model`, Certo routes each
  task to the best fit from your `models.yaml`, with fallback when a
  provider fails. No extra LLM call to decide.
- **Hard limits.** An iteration cap, a wall-clock budget across all retries,
  and an optional approve-every-action mode.
- **Scripts and CI.** Every failure state exits nonzero;
  `--require-verification` makes `inconclusive` fail too.
- **Sandboxed runs** with `--execution docker` (needs a source checkout
  for now; see known limits).
- **Server mode.** REST, WebSocket streaming, and an OpenAI-compatible
  `/v1/chat/completions` endpoint (`certo-server`).
- **Run records.** Transcript, token counts and cost per run, plus a log of
  which model was picked and why.
- **Skills.** A built-in catalog of lifecycle skills ships with the package;
  add your own conventions by dropping files in `./skills`.

## Install

```bash
pip install certo
```

With a local model (no API key):

```bash
export LLM_MODEL=ollama/qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434
certo "Build a CLI todo app in Python, with tests" --project todo
```

With a cloud model, set `LLM_MODEL` (for example
`anthropic/claude-sonnet-4-5-20250929`) and `LLM_API_KEY` instead. No `.env`
file is needed; exported variables are enough.

Optional extras: `certo[server]` for `certo-server`, `certo[sandbox]` for
Docker execution, and `certo[store-sqlite]`, `certo[store-redis]`,
`certo[store-mysql]` or `certo[store-postgres]` for server task persistence.

Requires Python 3.12+.

## Known limits

- `--execution docker` needs a source checkout for now: the agent-server
  image is built from the repo's Dockerfile, which isn't in the wheel.
  Build the image once from a clone, or point `CERTO_DOCKER_IMAGE` at a
  prebuilt one.
- Server mode has no authentication. Run it on localhost or behind your own
  gateway.
- Java projects are detected, but verification needs Maven or Gradle
  installed.
- Under Docker, automatic model selection makes the initial pick but does
  not fall back mid-task.
- Small local models can struggle with multi-step tool use. A coder-tuned
  model gives the best results.

The full list is in the
[manual](https://github.com/alessioricco/certo/blob/main/MANUAL.md#known-limitations).
