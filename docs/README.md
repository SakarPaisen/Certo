# Certo documentation

Certo is a coding agent that checks its own work. You give it a task. An
agent plans, edits files and runs commands until it says it is done. Then
Certo runs your project's real tests and build itself, with no AI involved,
and tells you if the work is really verified.

This page explains what Certo is and where to read next.

## Why Certo exists

Coding agents are confident, and often wrong about being finished. While
building Certo, an agent wrote a Tower of Hanoi game. Every unit test
passed. The game crashed the moment a player chose "solve". The agent said
the work was done, and so did the test runner.

Certo is built to catch that. When the agent stops, Certo:

1. runs the project's own checks (tests, build, lint, type checks) itself;
2. sends real failures back to the agent for another attempt;
3. stops early when a fix attempt changes nothing;
4. prints one verdict, such as `verified` or `retry_exhausted`, and exits
   with a code that scripts and CI can use.

The stories behind each of these checks are in
[Why agents lie](concepts/why-agents-lie.md).

## What Certo can do

- Work with almost any model: OpenAI, Anthropic, Google Gemini, Ollama on
  your own machine, or any model that [LiteLLM](https://docs.litellm.ai/docs/providers)
  supports. Switching is one setting.
- Verify Python, Node/JavaScript/TypeScript, Go, Rust and Java projects.
- Check a project with no agent and no model at all: `certo verify`.
- Pick the best model for each task from a list you write, and fall back to
  the next one when a provider fails.
- Enforce limits: an iteration cap, a time budget, and an optional "approve
  every action" mode.
- Run the agent in a Docker container, or as an HTTP server.
- Keep a record of each run: the full transcript, tokens and cost.
- Benchmark models on bundled tasks graded by hidden tests: `certo bench`.

## Where to go next

**New to Certo?** Start with [Getting started](getting-started.md). It
takes you from install to your first verified project.

**Want to do one specific thing?** Pick a guide:

| I want to... | Guide |
|---|---|
| Use OpenAI, Claude or Gemini | [OpenAI, Claude and Gemini](guides/openai-claude-gemini.md) |
| Use a model on my own machine | [Ollama and local models](guides/ollama-and-local-models.md) |
| Let the agent work on a project I already have | [Work on an existing project](guides/work-on-an-existing-project.md) |
| Answer the agent's questions, or approve each action | [Interactive and confirm mode](guides/interactive-mode.md) |
| Let Certo choose the model for each task | [Pick models automatically](guides/pick-models-automatically.md) |
| Check projects in CI | [Verify in CI](guides/verify-in-ci.md) |
| Add my own pass/fail rules for a task | [Acceptance checks](guides/acceptance-checks.md) |
| Run the agent inside a container | [Run in Docker](guides/run-in-docker.md) |
| Call Certo over HTTP | [Run as a server](guides/run-as-a-server.md) |
| See what a run did and what it cost | [Run records and costs](guides/run-records-and-costs.md) |
| Teach the agent my conventions, or give it new tools | [Add skills and tools](guides/add-skills-and-tools.md) |
| Measure which models and strategies really deliver | [Benchmark models and strategies](guides/benchmark.md) |

**Looking something up?** The reference pages are complete and exact:

- [Commands](reference/commands.md): every command, subcommand and flag.
- [Configuration](reference/configuration.md): every setting, its default,
  and where Certo reads it from.
- [Verdicts](reference/verdicts.md): every verification state and its exit
  code.
- [Verification by language](reference/verification-by-language.md): what
  Certo runs for each kind of project.
- [models.yaml](reference/models-yaml.md): the model list for automatic
  model selection and the benchmark.
- [bench.yaml](reference/bench-yaml.md): the benchmark file.
- [Server API](reference/server-api.md): every HTTP and WebSocket endpoint.

**Curious how it works?**

- [How verification works](concepts/how-verification-works.md)
- [Why agents lie](concepts/why-agents-lie.md)
- [Safety](concepts/safety.md)

**Something went wrong?** See [Troubleshooting](troubleshooting.md).

## Known limitations

- **Server mode has no authentication.** Run it on `127.0.0.1` or behind
  your own gateway. See [Safety](concepts/safety.md#server-mode).
- **Verification only knows what the checks test.** Untested features can
  be broken and still `verified`, and interactive menus are never
  exercised. See [How verification works](concepts/how-verification-works.md#what-verification-cant-do).
- **Some rules are only instructions to the model**, such as writing a
  `README.md` or not asking questions. A model can ignore them.
- **Covered languages:** Python, Node, Go, Rust and Java. Other projects,
  and standalone HTML pages, end `inconclusive`. Java needs Maven or Gradle
  installed. See [Verification by language](reference/verification-by-language.md).
- **Docker mode needs an image built from a source checkout**, and
  automatic model selection can't switch models in the middle of a Docker
  run. See [Run in Docker](guides/run-in-docker.md).
- **Small local models** often struggle with long, multi-step tasks. Coder
  models do best. See [Ollama and local models](guides/ollama-and-local-models.md).
- **Costs show as unknown** for models newer than your installed LiteLLM.
- **New, empty folders:** the agent starts with a Python environment only
  if the task mentions Python (or a Python tool such as pytest). Otherwise
  packages the agent installs may land outside the project's environment,
  and imports can fail during verification until they are installed again.
- **A Node project whose `test` script finds no test files counts as
  verified.** `node --test` and some other runners exit successfully when
  there is nothing to run. See
  [Verification by language](reference/verification-by-language.md#node-in-detail).
- **A task that is exactly the name of an existing file** in the current
  folder is read from that file.
- **Interactive mode covers only the first part of a task**, and neither it
  nor confirm mode works in server mode. See
  [Interactive and confirm mode](guides/interactive-mode.md).
- **The OpenAI-compatible endpoint** returns no verdict and doesn't replay
  chat history. See [Run as a server](guides/run-as-a-server.md#use-it-from-an-openai-compatible-client).
- **Third-party skill licenses** are detected with a simple text match,
  and only `SKILL.md` folders can be installed. See
  [Add skills and tools](guides/add-skills-and-tools.md#third-party-skills).

## For contributors

How to work on Certo itself, run its tests and make a release is in
[CONTRIBUTING.md](../CONTRIBUTING.md). Project status, the backlog and the
reasons behind design decisions are in [ROADMAP.md](../ROADMAP.md). The
original build plan is [SPEC.md](SPEC.md).
