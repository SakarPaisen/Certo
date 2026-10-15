# Certo v0.1.3

This release makes Certo work end to end when it's installed from PyPI.
(0.1.1 and 0.1.2 were never published; this is the first release after 0.1.0.)
The first real `uv tool install certo` run, with a local Ollama model,
found three problems that never showed up from the development
environment. All three are fixed, and a new release check now installs
every wheel the way users do before it can be published.

## Breaking change: `LLM_*` is now `CERTO_LLM_*`

Certo's LLM settings now use their own prefix, so they can't clash with
other tools that read `LLM_MODEL`:

| 0.1.0 | 0.1.3 |
| --- | --- |
| `LLM_MODEL` | `CERTO_LLM_MODEL` |
| `LLM_API_KEY` | `CERTO_LLM_API_KEY` |
| `LLM_BASE_URL` | `CERTO_LLM_BASE_URL` |
| `LLM_REASONING_EFFORT` | `CERTO_LLM_REASONING_EFFORT` |

The old names are no longer read at all. Rename them in your `.env` or
shell. If you forget, the "required" error names the old variables it
found and the rename to make.

## Fixes

- **Python projects get their own environment, and verification uses it.**
  Certo used to run a project's tests with its own interpreter. Installed
  from PyPI, that interpreter has no pytest, so verification could never
  pass, and the agent tried to install pytest into Certo's own
  environment. Now each Python project gets an isolated environment. Certo
  reuses an existing `.venv`/`venv` or `uv.lock` project, or creates
  `.venv` with `uv venv` or `python3 -m venv`. The agent's terminal uses
  it (`python`, `pip` and `pytest` resolve there), and so do pytest, ruff,
  mypy and the entry-point smoke run. If the project has tests but no
  pytest, Certo installs pytest into the project's environment and says
  so. If that install fails, the result is `unavailable`, not a test
  failure. Nothing is ever installed into Certo's own environment. Under
  `--execution docker`, the environment and the verification both live
  inside the container.
- **Models without a thinking mode work with no extra settings.** With
  `CERTO_LLM_REASONING_EFFORT` unset, the SDK's default reasoning effort was sent
  to every model. Ollama rejects it for models such as `qwen3-coder:30b`
  (`"qwen3-coder:30b" does not support thinking`), so the first call
  failed. Ollama models (`ollama/`, `ollama_chat/`) now get no reasoning
  parameter unless you set one. `CERTO_LLM_REASONING_EFFORT=none` or `off` turns
  reasoning off for any provider, and so do `--reasoning-effort`, the
  server fields and `models.yaml`.
- **No SDK banner.** The OpenHands SDK's nine-line startup banner no longer
  prints before Certo's output. Set `OPENHANDS_SUPPRESS_BANNER=0` to see
  it.

## New

- **`certo verify [PATH]`** runs the verification Certo runs after an
  agent, on any project and with no model: project detection, the
  project's environment, then every check, with the same
  `Verification: <state>` line and exit codes. `PATH` defaults to the
  current directory. A task such as `certo "verify the login flow"` still
  runs an agent.
- **`--version`** on `certo`, `certo-admin` and `certo-server`.

## For contributors

- `scripts/release_check.sh` builds the wheel and installs it with
  `uv tool install` into a throwaway tool directory. It then runs
  `certo verify` on passing, failing and dependency fixtures. The release
  workflow runs it on the exact wheel it publishes. `--with-llm` adds a
  real agent task.

## Upgrading

```bash
uv tool upgrade certo      # or: pip install -U certo
```

If you use `--execution docker` from a checkout, rebuild the image once
(`docker rmi certo/agent-server:local`). It carries a copy of Certo's tool
code.

The README's Ollama example now uses `qwen3-coder:30b` (roughly 20 GB of
GPU or unified memory). For less memory, `qwen2.5-coder:7b` is the smaller
option.
