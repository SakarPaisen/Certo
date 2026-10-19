# Certo

**The coding agent that doesn't take its own word for it.**

[![PyPI](https://img.shields.io/pypi/v/certo.svg)](https://pypi.org/project/certo/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/alessioricco/certo/blob/main/LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://github.com/alessioricco/certo/blob/main/pyproject.toml)
[![Built on OpenHands SDK](https://img.shields.io/badge/built%20on-OpenHands%20SDK-6f42c1.svg)](https://docs.openhands.dev/sdk)

Every coding agent eventually says *"Done! All tests pass."* Certo is the one that checks.

Give it a task. An agent plans, writes code and runs commands until it says it's finished. Then Certo runs your project's real tests and build **itself, with no AI involved**, sends real failures back for another try, and ends with one honest verdict and an exit code a script can trust. Any model, local or cloud. *Certo* is Italian for "sure".

```bash
pip install certo
certo init
cd certo-workspace && certo tasks/wordle.md --project wordle
```

```text
Verification: verified

Run summary:
  Total running time: 4m 03s
  Models: openai/gpt-5.6-luna
  Total tokens: 801,191 (input 774,063, of which cached 725,104; output 27,128)
  Total cost: $0.0593
```

## Agents say "done". Sometimes they're wrong.

Two real runs from building Certo, both asking a model for a Tower of Hanoi game:

- **"There are errors in the tests around sequence handling and state transitions."** The truth: the file didn't even run. An `IndentationError` stopped every test before it started. The agent never re-ran the tests; the diagnosis was made up.
- **Every unit test passed, and the game crashed the moment a user picked "solve".** The agent said success, and so did pytest.

The agent's report is a claim, not evidence. Certo looks at the evidence:

| When the agent... | Certo... | Verdict |
| --- | --- | --- |
| says it's done | runs the project's own tests, build, lint and typecheck | `verified` or a failure |
| left a check failing | sends the real error back and lets it try again | `retry_exhausted` if it never gets there |
| tries a fix that changes nothing | stops early instead of burning tokens | `no_progress` |
| "fixes" a bug without touching a file | asks once more, then refuses to call it verified | `unchanged` |
| leaves its own to-do list half done | doesn't run the checks at all | `incomplete` |
| builds something with no tests | never counts "nothing to check" as a pass | `inconclusive` |

Eight cases, and how each one changed Certo: [Why agents lie](https://github.com/alessioricco/certo/blob/main/docs/concepts/why-agents-lie.md).

## Numbers, not promises

How often would Certo have been fooled? `certo bench` measures it: each run is graded by **hidden tests the agent never sees**, and Certo counts every time it said `verified` while the hidden tests failed. From the Certo 0.1.15 benchmark (9 tasks, 7 models, 135 runs):

| Model | Hidden tests passed | Median time per task | Cost per solved task |
| --- | --- | --- | --- |
| `claude-sonnet-5-5` (cloud) | 9/9 | 31s | $0.12 |
| `claude-haiku-5-5` (cloud) | 9/9 | 45s | $0.0094 |
| `gemma4:31b-it-qat` (local, Ollama) | 26/27 | 12m 40s | $0.00 |
| `qwen3.8:27b` (local, Ollama) | 24/27 | 4m 37s | $0.00 |

Certo was fooled **3 times in 135 runs**: each time the code broke a rule the task stated, and the agent's own tests never tried it. When a model broke down (two local models often wrote their tool calls as text and did no work), Certo caught it: of 54 runs that failed the hidden tests, it said `verified` for only those 3. That's what the number is for: each fooled run shows a gap to close.

These tasks are small; harder ones are planned. All seven models, and the limits of this run: [Benchmark baseline 0.1.15](https://github.com/alessioricco/certo/blob/main/docs/benchmark/baseline-0.1.15.md).

## Quickstart

```bash
pip install certo
certo init
cd certo-workspace
certo tasks/wordle.md --project wordle
```

`certo init` asks which provider you use (OpenAI, Anthropic, Gemini, a local Ollama, or any LiteLLM model), takes your API key at a hidden prompt, saves the settings, and makes one real call to check the model works. It also leaves two sample tasks in `tasks/`: a terminal Wordle in Python and a browser Asteroids game (which needs Node 18+). With a cloud model a run uses your credits, and Certo prints the cost at the end. The generated project lands in `projects/wordle`.

Or work on one project at a time, new or existing:

```bash
cd any-project && certo "Add a --verbose flag, with a test"
```

This works in any folder when `certo init` saved your settings for "all projects on this computer", its default. Before the agent edits a folder that already has files, Certo prints a one-line warning if it has uncommitted git changes, or isn't a git repository. `certo check` shows where each setting comes from and re-runs the model check.

Already have a project? Check it with no agent and no model, for free:

```bash
certo verify ./my-project
```

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

The last line of every run is the verdict:

| State | Meaning |
| --- | --- |
| `verified` | The project's own tests or build ran and passed. |
| `inconclusive` | Nothing could be checked (no tests yet, unknown project type, missing toolchain). |
| `unchanged` | The checks passed, but the agent changed no file, so they don't show the task was done. |
| `retry_exhausted` | A check kept failing after the automatic fix attempts. |
| `no_progress` | A fix attempt changed nothing in the failing output, so Certo stopped early. |
| `incomplete` | The agent left items on its own to-do list unfinished. |
| `budget_exhausted` | The task ran out of its time budget. |

The exit code is nonzero for every failure state, so Certo works in scripts and CI. Add `--require-verification` to make `inconclusive` and `unchanged` fail too. Every state and its exit code: [Verdicts](https://github.com/alessioricco/certo/blob/main/docs/reference/verdicts.md). What to do next, verdict by verdict: [After the verdict](https://github.com/alessioricco/certo/blob/main/docs/guides/after-the-verdict.md).

## Features

**Checks you can trust**

- **Independent verification.** Re-runs the project's real test, build, lint and typecheck commands after the agent finishes. It never invents a command the project doesn't configure.
- **Works across languages.** Detects and verifies Python, Node/JS/TS, Go, Rust and Java (Maven/Gradle) projects. Each Python project gets its own virtual environment, used by both the agent and the checks.
- **Verify without an agent.** `certo verify [PATH]` runs the same checks on any project, with no model needed.
- **Hard limits.** An iteration cap, a wall-clock budget across all retries, and an optional approve-every-action mode.

**Any model, used well**

- **Any model, one setting.** Ollama, Anthropic, OpenAI, Gemini, DeepSeek or Moonshot. Switching is one environment variable.
- **Escalates only when it must.** Give Certo a ladder of models, cheapest first. Each task starts on the first, and moves to a stronger model only when verification shows the cheaper one couldn't finish. Add `--escalate`. See [Escalate between models](https://github.com/alessioricco/certo/blob/main/docs/guides/escalate-between-models.md).
- **Picks the best model per task.** Rate your models in `models_list.yaml`, enable the ones you have keys for in `models.yaml`, and Certo routes each task to the best fit, with fallback when a provider fails. No extra LLM call to decide. Add `--auto-model`.
- **A benchmark.** `certo bench` compares models and strategies on tasks graded by hidden tests, and counts how often Certo itself was fooled. See [Benchmark models and strategies](https://github.com/alessioricco/certo/blob/main/docs/guides/benchmark.md).

**Fits how you work**

- **Resume.** `certo --resume "hint"` continues a run with its earlier conversation, or with a stronger `--model`.
- **Run records.** Full transcript, token counts and cost per run, plus a log of which model was picked and why.
- **Sandboxed runs** ([experimental](https://github.com/alessioricco/certo/blob/main/docs/README.md#experimental-features)). Add `--execution docker` to run the agent in a container.
- **Server mode.** REST and WebSocket streaming. The OpenAI-compatible `/v1/chat/completions` endpoint and the SQL and Redis task stores are [experimental](https://github.com/alessioricco/certo/blob/main/docs/README.md#experimental-features).
- **Skills and custom tools.** Add project conventions or new tools by dropping files in a folder. Installing third-party skills is [experimental](https://github.com/alessioricco/certo/blob/main/docs/README.md#experimental-features).

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

Certo is built on the [OpenHands Software Agent SDK](https://docs.openhands.dev/sdk), which runs the agent loop and tools. Certo adds the parts the SDK leaves open: what counts as verified, which model runs and when to fall back, the budgets, and the CLI and server you talk to. The details: [How verification works](https://github.com/alessioricco/certo/blob/main/docs/concepts/how-verification-works.md).

## Known limits

- Server mode has no authentication. Run it on localhost or behind your own gateway.
- Java projects are detected, but verification needs Maven or Gradle installed.
- Docker execution, the OpenAI-compatible endpoint, the SQL and Redis task stores and third-party skills are [experimental](https://github.com/alessioricco/certo/blob/main/docs/README.md#experimental-features): tested, not yet proven in real use. Under Docker, automatic model selection makes the initial pick but does not fall back mid-task.
- Small local models can struggle with multi-step tool use. A coder-tuned model gives the best results.
- `verified` proves what the project's tests test, and nothing more. Read the tests: [Write a task Certo can check](https://github.com/alessioricco/certo/blob/main/docs/guides/write-a-good-task.md).

The full list is in the [documentation](https://github.com/alessioricco/certo/blob/main/docs/README.md#known-limitations).

## Documentation

- [Documentation home](https://github.com/alessioricco/certo/blob/main/docs/README.md): guides, reference and concepts, organised by what you want to do
- [Getting started](https://github.com/alessioricco/certo/blob/main/docs/getting-started.md): install, `certo init`, your first task, and reading the verdict
- [Write a task Certo can check](https://github.com/alessioricco/certo/blob/main/docs/guides/write-a-good-task.md): the habits that turn a vague request into a verified result
- [Troubleshooting](https://github.com/alessioricco/certo/blob/main/docs/troubleshooting.md): the problems people actually hit, with their fix
- [Why agents lie](https://github.com/alessioricco/certo/blob/main/docs/concepts/why-agents-lie.md): the real cases of agents claiming "done", and how Certo catches each one
- [ROADMAP.md](https://github.com/alessioricco/certo/blob/main/ROADMAP.md): where Certo is going; [TODO.md](https://github.com/alessioricco/certo/blob/main/TODO.md): what's left to do

## Contributing

Issues and pull requests are welcome. Issues labelled [good first issue](https://github.com/alessioricco/certo/labels/good%20first%20issue) are a good place to start, and so is [adding a benchmark task](https://github.com/alessioricco/certo/blob/main/docs/guides/contribute-a-benchmark-task.md). To work on the code:

```bash
git clone https://github.com/alessioricco/certo.git
cd certo
uv pip install -e ".[dev]"
uv run pytest -q     # no API key needed
```

## License

[MIT](https://github.com/alessioricco/certo/blob/main/LICENSE). Built by [Alessio Ricco](https://github.com/alessioricco).
