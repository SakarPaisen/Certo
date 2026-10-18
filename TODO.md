# TODO

Everything still to do, so nothing is forgotten. One entry per item: what,
why, and when it counts as done. Where Certo is going, and why these
items, is in `ROADMAP.md`; why past choices were made is in `DECISIONS.md`.

> **Maintenance note:** add an item the moment it is found (a bug, a
> deferred step, an idea). When it is done, delete it in the same change,
> and record the decision in `DECISIONS.md` if it was a non-obvious one.
> Git history and the release notes keep what was done. See `CLAUDE.md`.

Sections follow the themes in `ROADMAP.md`. Inside each section, the
first item is the suggested next one.

## Before the next release

- **Ship `bench.yaml.example` in the wheel.** It is only in the sdist
  (repo root); the model examples moved to `src/certo/examples/` in
  0.1.10. Ship it there, make a missing `bench.yaml` print the `cp`
  command (as `model_files.missing_message()` does), replace the `curl`
  download step in `docs/guides/write-a-benchmark-file.md` with that `cp`
  command, and update the sdist allowlist and `tests/test_packaging.py`.
  Feature: bump the version. Deferred on 2026-10-18 while a benchmark ran
  from the checkout. While there: the example (and the example
  `models.yaml`) enables `qwen3.6-35b-local`, which scored 0/27 in the
  0.1.15 local benchmark (tool calls written as text); consider
  `qwen3.8-27b-local` instead.
- **Benchmark 0.1.14–0.1.15 on a local and a cloud model** (working
  agreement 2). `unchanged` and bench transcripts are unit-tested only.
  The 0.1.11 derived-ladder order is not benchmarked either. Done when a
  results folder from this version has both kinds of arm. Local half done
  (`docs/benchmark/local-models-0.1.15.md`); the cloud arms were started
  2026-10-18.
- **Point code comments at the new planning files.** About 41 comments in
  `src/` and `tests/` say "see ROADMAP.md (decisions log / known
  limitations)"; those sections are now `DECISIONS.md` and
  `ARCHITECTURE.md`. Comments only. Deferred on 2026-10-18 while a
  benchmark ran from the checkout.
- **Run `scripts/release_check.sh`** against the built wheel.
- **Publish** (the Author does it): `main` is ahead of origin; PyPI has
  0.1.10.

## 1. Prove it

- **A baseline per release.** `docs/benchmark/baseline-<version>.md` for
  every release (local vs cloud, fooled rate, cost per solved task), and
  a README badge. Only `baseline-0.1.13.md` exists.
- **Bench task set v2: app-scale tasks.** Multi-file, multi-language: Go
  REST API with a database, React frontend + API, Rust CLI with
  subcommands, a fix inside an existing mid-size repo. Grading supports
  only Python and Node, with no packages, so Go/Rust tasks need grading
  support first. Bump the task-set `VERSION`. Today's 9 tasks don't
  separate a local 27B model from a cloud one.
- **Escalation has never climbed in a benchmark.** The 0.1.13 baseline
  ended every run on rung 1, so climbing, the handoff and derived-ladder
  ordering are unmeasured. Needs task set v2.
- **Milestone 3: the live provider-swap proof.** One task with two
  `CERTO_LLM_MODEL` values (a local and a cloud model exist since
  2026-10-17). Not blocked any more, just not run.
- **Re-verify the "confident but wrong" fixes live**: #1, #2, #4, #5, #6
  and #10 in `ARCHITECTURE.md` say "not re-verified live". At least the
  ones a benchmark task can reach.
- **Pull-request CI with tests and a ruff gate.** Only `release.yml`
  exists, and `main` has lint/format findings (`server.py`, tests) to
  clear first. Add `release_check.sh` to it too.
- **Docker verification has never run against a real container**, and
  neither has escalation under Docker. Fake-workspace tests only.
- **`tests/test_bench_tasks.py` fixes the task-set size** (8–10 tasks,
  2–3 in Node), so any contributed task fails it. Loosen it, or make it
  check per-task rules only. `docs/guides/contribute-a-benchmark-task.md`
  tells contributors to update it until then.

## 2. Complex tasks

- **Milestone mode.** Split a big task into milestones, each with its own
  acceptance checks, run and verified one at a time, building on
  `--resume`/`STATUS.md`. The main step from "small task" to "app".
- **Independent acceptance tests from the spec.** Before building, a
  separate conversation (optionally another model) writes tests from the
  task text only; the builder may not edit them. Brings the benchmark's
  hidden-test idea to real runs.
- **Protect verification files from silent agent changes.** The agent can
  weaken or delete tests, build scripts or lint config before Certo
  verifies; only prompts discourage it (golden rule 6 gap). Record those
  files before the run, compare after, and report or reject changes the
  task didn't ask for. Needs a policy for legitimate test changes.
- **Context management for long runs.** The SDK's own condensing
  (verify-first), plus a warning when a local model's context window is
  too small for the task (qwen3.8 at 32K).
- **Checkpoints and rollback.** A git snapshot per fix attempt and per
  escalation rung, so a bad attempt can be undone.
- **Escalation "restart" mode.** Copy the original files back before the
  next rung, instead of continuing in the same files.
  `_stream_escalation` already lists the workspace before each rung.

## 3. Languages and verification

- **Run-the-app verification.** Start a server and probe an HTTP
  endpoint; build a frontend and load it in a headless browser (the SDK
  ships a browser tool) for a blank page or console errors.
- **Node: "no tests" counts as verified.** `node --test` exits 0 with no
  test files, so `npm test` passes. Found by the first bench integration
  run (2026-10-16). Documented, not fixed.
- **Rust: missing clippy fails the project.** `cargo clippy` is planned
  whenever `cargo` exists; without the component it is `failed` (exit
  101) instead of `unavailable`. Workaround in `docs/troubleshooting.md`.
- **Node: detect jest/vitest/mocha.** Today `build`/`test` scripts run as
  opaque commands; the runner and its results aren't parsed.
- **Node: infer ESLint/`tsc` from config**, as `_ruff_configured()` does
  for Python. Flat-config variants make this harder than the Python case.
- **Java: a Maven/Gradle toolchain** in the Docker image and the dev
  environment. Java is detection-only in both today.
- **New ecosystems**, in order: C#/.NET, PHP (Composer), Ruby, Kotlin/
  Android (Gradle), C/C++ (CMake), Swift.
- **Check that the agent-facing `run_tests` tool is timeout-safe.** An old
  item said its pytest/npm paths used bare `subprocess.run`; they now go
  through `runner.run(..., timeout=300)`. Confirm timeouts and a missing
  executable return an observation instead of raising, add tests, close.
- **Interactive programs can't be driven** (menus, `SOLVE`-style choices).
  Deliberately not built: no safe general way to guess input. Would need
  the agent to declare an interaction script. Keep as a known gap unless
  a design appears.

## 4. Models and strategies

- **Tool calls written as text.** In the 0.1.15 local benchmark, every
  failed `qwen3.6` and `qwen3.8` run and 18 of 22 failed `devstral` runs
  ended because the model wrote its tool call as JSON in a text answer;
  the SDK took it as the final message. First find the cause (Ollama chat
  template, or context too small for the tool definitions): rerun one
  task with a known `OLLAMA_CONTEXT_LENGTH`. Then consider a harness fix:
  when the final message parses as a tool call, send it back once as a
  correction. Gated by tier or opt-in, and benchmarked local and cloud.
- **Record the Ollama setup in bench results.** `meta.json` has no Ollama
  version or context length, so a local result can't be traced to the
  setup (`/api/version`, `/api/ps`). Done when the report shows both.
- **Slow local models lose correct work to the time budget.** Three runs
  in the 0.1.15 local benchmark passed the hidden tests but ended
  `budget_exhausted`. Consider a per-arm budget in `bench.yaml`. Also: a
  `devstral` run (`token-bucket` r3) ran 57 minutes under the 30-minute
  budget; find why the budget overran (a single long model call?).
- **Bench estimates from recorded cost.** The plan prices every run at a
  fixed ~500k input / ~20k output tokens (far too high: a cloud run used
  ~124k in the baseline). Use the per-model average from earlier
  `cost.json` files in the same parent folder; guess only for models with
  no history.
- **Move task profiles and escalation ladders out of `models_list.yaml`**
  into an optional `model_policy.yaml` (user's idea, 2026-10-17). The list
  keeps only shared catalog data; the policy holds `task_profiles:` and
  `escalation:`. Same lookup as the other files; built-in defaults when
  missing; read the old sections for a version or two with a warning;
  `catalog_check` validates across both; `bench.yaml` gains
  `model_policy_file`. Feature bump; docs: models-yaml reference, both
  model guides, the auto-model/escalation concept page.
- **A cost ceiling for single-model runs.** `CERTO_MAX_TASK_COST`
  applies to escalation only (checked before each rung), and bench has
  `--max-cost`; a plain run is bounded by time and iterations, not money.
  The conversation's metrics carry the running cost, so it could be
  checked between retries, ending in a new verdict.
- **Bench strategy `best_of`**: N attempts, the verifier picks. Next entry
  in `bench_strategies.STRATEGIES`. Benchmark on local and cloud before
  release.
- **Per-tier tuning for small models.** Shorter prompts and stricter
  tool-call repair, gated by model tier and measured on both tiers.
- **`certo doctor` for Ollama**: model pulled, context size, thinking
  mode, measured tokens per second.
- **Measured speed and context in the catalog**, filled from real runs,
  so ladders can weigh speed. A `speed` rating would count as capability
  today.
- **Auto-model: a quality failure falls back to the next-best fit, not a
  more capable model.** Escalation (0.1.9) answers this for `--escalate`;
  `--auto-model`'s chain still walks one ranked-by-fit list. Decide
  whether auto-model should climb by capability on a verification
  failure, or point users to `--escalate`.
- **Auto-model: no mid-task fallback under Docker.** `RemoteConversation`
  has no public `switch_llm`. Revisit when the SDK adds one.
- **Auto-model: switching to a model with a smaller context window**
  surfaces as a context-overflow error (which then falls through to the
  next candidate). A condenser, or ordering to avoid it, would be cleaner.
- **Auto-model: per-sub-step model choice** (a cheap model for
  scaffolding, a strong one for the hard part), hooked on `task_tracker`
  items. Needs interrupting a run mid-call; open design.
- **Preview model choice without a run**: `certo check` shows ladders, but
  nothing shows which task profile and ranking `--auto-model` would pick
  for a given task text (`classify_task`/`rank_candidates` are pure).
- **Other SDK reasoning fields** (`reasoning_summary`,
  `extended_thinking_budget`, `enable_encrypted_reasoning`): left unwired
  on purpose (provider-specific). Only if a provider needs one.

## 5. Adoption

- **A first run in minutes, with one model.** No catalog, no ladders:
  `certo init`, then a first verified project. Getting started shows only
  that path. Measure it: time from `pip install` to the first `verified`,
  on a clean machine.
- **Mark the less central parts as experimental in the docs**: the
  server's SQL and Redis stores, the OpenAI-compatible endpoint,
  third-party skills, Docker execution. They stay, but stop setting the
  pace.
- **GitHub Action**: an issue labelled `certo` becomes a pull request with
  the verdict and checks in its description.
- **Docs articles still to write** (ideas from 2026-10-18): build an
  app in several tasks (needs real runs); review the agent's work safely;
  share your benchmark results; keep costs down; use `certo verify`
  without the agent (pre-commit, any AI tool).
- **Prebuilt Docker image.** Docker execution from a pip install fails:
  `workspace.py` builds from `docker/agent-server.Dockerfile` relative to
  the repo, which isn't in the wheel. Ship the Dockerfile and tool source
  as package data, or publish an image. Documented in
  `docs/guides/run-in-docker.md`.
- **`certo init models`**: a setup helper for `models_list.yaml`/
  `models.yaml`. Find provider keys and Ollama models, copy the example
  list, offer only entries the user can run (never invent ratings), write
  keys as `${VAR}` (verify `models.yaml` expands it first), test each with
  the `check --models` call and deactivate failures, print the ladder. The
  first run must still need no model files.
- **`certo models update`**: compare the shipped example catalog with the
  user's `models_list.yaml` and offer to merge.
- **MCP server**, so Claude Desktop, Cursor, Zed and others can call Certo
  as a tool and get the verdict back.
- **Run report**: an HTML/Markdown summary per run (what changed, which
  checks ran, cost, why the verdict), from the existing artifacts.
- **Live progress view** in the terminal: current milestone, last check,
  cost so far.
- **Docs website and gallery**: a site generator for `docs/`, a gallery of
  apps built with Certo (verdict and cost each), a short demo video.

## 6. Server mode

- **No authentication.** Bound to `127.0.0.1` by default, but with
  `--host` every endpoint is open: `POST /tasks` runs an agent with a
  terminal (shell access on the host), and requests may override
  `api_key`/`base_url` with no validation. Minimal fix: a shared-secret
  header (e.g. `CERTO_SERVER_API_KEY`) checked on every task route, and a
  loud docs warning against a public `--host` without it.
- **WS and `/v1/chat/completions` file artifacts under `_unscoped`.** They
  call `stream_task` without `run_id`/`project`, so with
  `CERTO_ARTIFACTS_DIR` set their records land in `_unscoped/<uuid>` even
  when a `project` was sent. Only `POST /tasks` files them correctly.
- **`/v1/chat/completions` has no verdict.** Its wire format has no field
  for `verification_state`, so a caller gets the agent's own claim only.
  Needs a deliberate wire-format choice (a custom field, or a trailing
  message).
- **`/v1/chat/completions` always reports zero token usage**, although
  the conversation's metrics have the counts.
- **`model_decisions` isn't on `GET /tasks/{id}`.** The SQL stores need a
  new column; the `rungs` column (0.1.9) already shows how
  (`ALTER TABLE ... ADD COLUMN` on startup).
- **No way to list tasks or projects** in a task store (`certo-admin`,
  REST): every operation needs a known id or project name.
- **ECS/EC2 or other remote execution backends.** `build_workspace()` is
  the single dispatch point. No concrete need yet.

## 7. Built-in skills to make

Rules for every new skill: short and narrowly triggered (prefer `paths:`
triggers; every skill that fires costs context a 32K local model can't
spare); measured with `certo bench` on a local and a cloud model before
release; authored for Certo in the legacy `triggers:`/`paths:` format.
Today there are 12 (eight `lifecycle/`, `git/commit-conventions`,
`python-web/fastapi-conventions` and `pin-dependencies`,
`testing/pytest-conventions`).

**Make a project verifiable** (first; suggested order: the first three):
- `testable-interactive-apps`: logic apart from input/output, so games
  and menus are testable. Triggers: game, interactive, menu, terminal.
- `python-environment`: use the project's `.venv`; never install into
  Certo's interpreter or with `pip install --user`; declare dependencies
  in `pyproject.toml` first.
- `node-project-setup`: a real `test` script with at least one test, a
  `build` script, a committed lockfile, no interactive scaffolders.
- `cli-entry-points`: `__main__` guard last, a closed stdin doesn't hang,
  `--help` and non-interactive flags work.
- `test-oracles`: derive expected values independently, never from the
  implementation's output; check a suspicious test against its own setup
  before re-editing correct code. Maybe a section of
  `lifecycle/testing-and-verification` instead.

**Languages** (path-triggered, one per verified ecosystem): Go (`go.mod`),
Rust (`Cargo.toml`, with the clippy gotcha), Java (commit the wrapper),
TypeScript (`tsc --noEmit` as a `typecheck` script), Python (extend
`pytest-conventions` with ruff/mypy setup); new ecosystems get one when
their verification lands.

**Frameworks** (each with a recipe to build, test and smoke-check):
Vite/React, Next.js, Express, Django, FastAPI (extend
`fastapi-conventions`), Spring, Rails, Laravel.

**App building blocks**: `http-api-testing` (the framework's test client,
no real network), `database-basics` (SQLite, migrations, an isolated test
database).

## Smaller bugs

- **Traceback when a benchmark ends.** After the results are written,
  the SDK's terminal reader thread logs `PTY reader thread error: [Errno
  9] Bad file descriptor` (`subprocess_terminal.py`): it reads a terminal
  that was already closed. Harmless but alarming; users read it as a
  crash. Close the conversations' terminals before exit, or silence it.
- **`llm_check.explain()` always says "in .env"** ("Check
  CERTO_LLM_API_KEY in .env"), although since 0.1.5 the value usually
  comes from the user settings file or the environment.
- **Third-party skills: narrow license detection, `SKILL.md` only.** Eight
  permissive licenses are recognised; anything else is `unknown` and needs
  acknowledgement. Legacy single-file upstream skills can't be installed.
  Fine for now; revisit if people use the feature.
