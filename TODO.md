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

- **A recorded demo of escalation on a provider failure.** Urgent: it
  checks live an assumption Certo's escalation rests on, that `--escalate`
  climbs to the next rung when a provider fails. Only `--auto-model`'s
  switch on a provider failure has been seen live (2026-10-19). A short GIF
  for the top of the README: a task moves to another provider's model
  when the first fails, and still ends `verified`. Setup: a two-rung
  ladder across providers in `escalation.yaml` (for example
  `claude-sonnet-5-5` → a cheap OpenAI model), with an invalid key for
  rung 1 in `models.yaml`; the bundled Wordle task, with `--escalate`.
  Dry run first: check what Certo prints when a rung fails on a provider
  error. If the line is unclear or buried, improve it before recording (a
  one-liner naming the failed model, the reason and the next rung): a
  code change, with docs and tests. Alessio records the real run with
  asciinema and converts it to a GIF. Add a record page for that run
  under `docs/benchmark/`, like `escalation-wordle-0.1.19.md`, and link
  the GIF to it. The caption says rung 1's key was rejected for the demo;
  don't call it an outage. Related: a small `certo bench` run of the
  Haiku → Sonnet ladder, so the README can drop one "not benchmarked
  yet". Done when the GIF is in the README, linked to its record page.
- **README wording: no comparisons with other agents, no local-first
  leftovers.** Two fixes, with the matching `docs/` pages in the same
  commit:
  1. "Any model, and the right one for each task" opens with "Most coding
     agents are built around one provider." Certo shouldn't claim what
     other agents do or don't do: say it about Certo only, for example
     "Certo isn't tied to any provider: the model is one setting…". While
     there, search the README and `docs/` for other comparative claims
     ("most agents", "other agents", "unlike", "the only", "the first")
     and rewrite them the same way.
  2. "Why the verdict can be trusted" says the verdict "decides when a
     local model's work is good enough to keep", a leftover from the
     local-first positioning. Make it "a model's work".

  Done when neither sentence is left and the search finds no other
  comparative claim.
- **Unpin the release runner from `ubuntu-24.04`.** Pinned for 0.1.18
  because `ubuntu-latest` moved to Ubuntu 26 on 2026-10-19. Switch the
  three jobs back once a run on `ubuntu-latest` has passed (the
  pull-request CI below, when it exists, is the cheapest place to try).
  While there, check the 0.1.18 release run showed no Node.js 20 warning.

## 1. Prove it

- **A baseline per release.** `docs/benchmark/baseline-<version>.md` for
  every release (local vs cloud, fooled rate, cost per solved task), and
  a README badge. 0.1.13, 0.1.15 and 0.1.18 (local only) exist; no badge
  yet. A `qwen2.5-coder:7b` arm would replace "unmeasured" for the
  small-machine suggestion.
- **Bench task set v2: app-scale tasks.** Multi-file, multi-language: Go
  REST API with a database, React frontend + API, Rust CLI with
  subcommands, a fix inside an existing mid-size repo. Grading supports
  only Python and Node, with no packages, so Go/Rust tasks need grading
  support first. Bump the task-set `VERSION`. Today's 9 tasks don't
  separate a local 27B model from a cloud one. Contributed tasks in the
  current format help meanwhile: [#3](https://github.com/alessioricco/certo/issues/3).
- **Escalation after a `failed` rung is unmeasured.** The 0.1.17
  escalation run climbed 10 times, all past a model that did no work.
  Climbing after a failed verification, the handoff of half-done work and
  derived-ladder ordering are still unmeasured. Needs task set v2. Candidate ladder from the
  0.1.15 local benchmark: `qwen3.8-27b-local` → `gemma4-31b-qat-local` →
  a cloud model (qwen3.8 is about 3× faster; gemma never wrote tool calls
  as text, qwen3.8's only failure mode). Bench it as three arms: each
  model alone, and the ladder.
- **An `inconclusive` rung that wrote code but no tests stops the
  ladder.** 0.1.17 escalation run, `q36-ladder` · `temperature-table`:
  qwen3.6 wrote the module, then its test file as a text tool call, so
  nothing could be checked and haiku was never asked. Decide whether a
  rung whose last message is a tool call written as text should climb.
  Two options to discuss (2026-10-19): just climb, or climb and ask the
  next rung to write the missing tests first. Done when decided
  (DECISIONS.md) and, if yes, tested.
- **Re-verify the "confident but wrong" fixes live**: #1, #3, #5, #10
  and #6 for Java in `ARCHITECTURE.md` say "not re-verified live" (#2, #4
  and #6 for Go/Rust were, 2026-10-19). #1 and #5 are hard to trigger on
  purpose; #10 is reachable from a benchmark task.
- **Pull-request CI with tests and a ruff gate.** Only `release.yml`
  exists, and `main` has lint/format findings (`server.py`, tests) to
  clear first ([#2](https://github.com/alessioricco/certo/issues/2), a starter issue). Add `release_check.sh` to it
  too.
- **Move the historical planning docs into `docs/history/`**
  (`docs/KICKOFF.md`, `docs/SPEC.md`, `docs/ROADMAP.txt`), so readers
  don't take them for current docs; fix every reference. Starter issue:
  [#4](https://github.com/alessioricco/certo/issues/4).
- **Docker verification has never run against a real container**, and
  neither has escalation under Docker. Fake-workspace tests only.

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

- **Windows: the tests and Python verification assume the macOS/Linux
  virtual environment layout** ([#7](https://github.com/alessioricco/certo/issues/7),
  reported in #6). `tests/conftest.py:32` globs `lib/python*/site-packages`
  (Windows: `Lib\site-packages`), so the suite can't run there;
  `project_env.py` uses `.venv/bin/python` (Windows:
  `.venv\Scripts\python.exe`), so verifying a Python project probably
  fails too. Never tried. Done when the suite passes on Windows and the
  Known limitations line in `docs/README.md` can go.
- **Run-the-app verification.** Start a server and probe an HTTP
  endpoint; build a frontend and load it in a headless browser (the SDK
  ships a browser tool) for a blank page or console errors.
- **Node: "no tests" counts as verified.** `node --test` exits 0 with no
  test files, so `npm test` passes. Found by the first bench integration
  run (2026-10-16). Documented, not fixed.
- **Node: detect jest/vitest/mocha.** Today `build`/`test` scripts run as
  opaque commands; the runner and its results aren't parsed.
- **Node: infer ESLint/`tsc` from config**, as `_ruff_configured()` does
  for Python. Flat-config variants make this harder than the Python case.
- **Java: a Maven/Gradle toolchain** in the Docker image and the dev
  environment. Java is detection-only in both today.
- **New ecosystems**, in order: C#/.NET, PHP (Composer), Ruby, Kotlin/
  Android (Gradle), C/C++ (CMake), Swift.
- **Interactive programs can't be driven** (menus, `SOLVE`-style choices).
  Deliberately not built: no safe general way to guess input. Would need
  the agent to declare an interaction script. Keep as a known gap unless
  a design appears.

## 4. Models and strategies

- **Live check of the auto-model quality fallback.** The provider-failure
  switch ran live on 2026-10-19 (ARCHITECTURE.md). The other path, a fix
  attempt that still fails the checks, has only run against a fake; it
  needs a model that fails on purpose, so it may take a few tries.
- **A `certo bench` strategy for `--auto-model`.** Only `single` and
  `escalate` exist (`bench_strategies.py`), so the README can say auto-model
  is unmeasured but not show a number. Add an `auto` strategy (task
  profiles plus fallback, as the CLI runs it) and bench it next to the
  single models and a ladder.
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
  Starter issue: [#5](https://github.com/alessioricco/certo/issues/5).
- **Slow local models lose correct work to the time budget.** Three runs
  in the 0.1.15 local benchmark passed the hidden tests but ended
  `budget_exhausted`. Two causes, found 2026-10-19 (documented in
  configuration and troubleshooting, not fixed):
  - **Certo doesn't check the work once the budget is gone**
    (`_verify_and_report` returns `budget_exhausted` first). The checks
    need no model; running them would turn these into `verified` or a
    real failure. Decide whether the verdict should then be `verified`
    or stay `budget_exhausted` with the check results shown.
  - **The budget can't stop a run in progress.** It is checked only
    before each `.run()`; one run makes up to 50 model calls, each up to
    `CERTO_LLM_TIMEOUT_SECONDS` × 6 attempts (the SDK retries timeouts 5
    times). `devstral` `token-bucket` r3 (timeout 1200s) wrote its files
    in the first 6 minutes, then spent ~50 on 4 calls: 57 minutes in all.
    Unproven, since bench transcripts carry no timestamps; add them.
    Fix by pausing the conversation at the deadline (SDK
    `conversation.pause()`, verify first) and capping the per-call
    timeout at the time left.
  Also consider a per-arm budget in `bench.yaml`.
- **Bench estimates from recorded cost.** The plan prices every run at a
  fixed ~500k input / ~20k output tokens (far too high: a cloud run used
  ~124k in the baseline). Use the per-model average from earlier
  `cost.json` files in the same parent folder; guess only for models with
  no history.
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

Walked through as a new user on 2026-10-20 (certo 0.1.20 from PyPI, an
empty home folder, Ollama on another machine). `certo init` took 16s and
the first task, Wordle, ended `verified` in 11m 49s. What got in the way
is in the first item and in "Smaller bugs". (The quieter run, 0.1.21,
cut that first run's output from 2,949 lines to 1,021.)

- **`certo init` sets up more than one model, in menus, and runs a
  first task.** Today a second model means: copy three examples from
  deep inside the tool's install folder (`certo check` prints the `cp`
  commands only once a model file exists, although the pick-models guide
  says it prints them when one is missing), then edit 600 lines of YAML.
  The copied `models.yaml` is live at once: three models enabled, one at
  a made-up `192.168.1.50`, one cloud model with an empty key, and
  `certo check` warns only about the key. The model `init` already saved
  has to be entered again, under another name. Instead, `init` (or `certo
  init models`) offers a navigable menu (arrow keys; `prompt_toolkit` and
  `rich` come with the SDK already, so declare them as Certo's own
  dependencies before using them): start from the model already saved,
  offer models from the example list for the keys and Ollama models it
  finds, never invent ratings, take keys at a hidden prompt into the
  settings file and name them in `models.yaml` as `${VAR}`, test each one with the `check --models`
  call and leave failures disabled, write only the models that work, then
  show `certo check`'s profile table. At the end it offers to run one
  sample task, so the user sees a verdict without typing another command.
  The plain one-model path must stay as short as it is. Done when a new
  user gets from `uv tool install` to an `--auto-model` run without
  editing a file, measured like the first run.

  Agreed with the Author on 2026-10-20 (screens reviewed as mockups):
  - "Add more models?" defaults to No, and the last screen always offers
    "Just one model, without --auto-model or --escalate" (which one, from
    the models set up) as the default, besides `--auto-model` and
    `--escalate` as the mode for every run.
  - Every list (provider, Ollama model, extra models) ends with "Another
    model": a typed LiteLLM id, tested like the others. A model that
    isn't in the example list gets ratings from the user (1 to 5, Enter
    keeps 3), saved as "rated by you"; without them it can be used only
    alone.
  - Keys stay only in the settings file; `models.yaml` refers to them as
    `${VAR}` (see DECISIONS.md).
  - `models_list.yaml` is the example list, copied unchanged, kept up to
    date by `certo models update`.
  - Order, one commit each: `${VAR}` in `models.yaml` (done, 0.1.21);
    `certo init models` (extra models, testing, the preview and the mode;
    done, 0.1.21); `certo models update` (done, 0.1.21); menus for all
    of `init` (done, 0.1.21); the sample run (done, 0.1.21). Left: the
    "Done when" measurement, a new user from `uv tool install` to an
    `--auto-model` run, timed like the first run, once 0.1.21 is on
    PyPI.
- **A first run in minutes, with one model.** No catalog, no ladders:
  `certo init`, then a first verified project. Getting started shows only
  that path. Measured 2026-10-19 in an empty home folder: 88.5s from
  `uv tool install` to `verified` (`docs/benchmark/first-run-0.1.19.md`).
  Still to do: a truly clean machine (no Python, no uv).
- **Fast start-up.** `certo --version` takes ~3s (18.6s on the very first
  run, compiling bytecode): `certo.cli` imports the SDK at the top
  (~2.6s). Import it only for the commands that run an agent, so
  `--version`, `verify` and `check` start at once.
- **GitHub Action**: an issue labelled `certo` becomes a pull request with
  the verdict and checks in its description.
- **Docs articles still to write** (ideas from 2026-10-18): build an
  app in several tasks (needs real runs); review the agent's work safely;
  share your benchmark results (with the benchmark file, as `docs/benchmark/` does); keep costs down; use `certo verify`
  without the agent (pre-commit, any AI tool).
- **Prebuilt Docker image.** Docker execution from a pip install fails:
  `workspace.py` builds from `docker/agent-server.Dockerfile` relative to
  the repo, which isn't in the wheel. Ship the Dockerfile and tool source
  as package data, or publish an image. Documented in
  `docs/guides/run-in-docker.md`.
- **A secret manager for keys** (an idea, 2026-10-20). Keys live only in
  the settings file for now. Later, read them from the system keychain
  or a secret manager (1Password, Bitwarden, a cloud vault) instead.
  Decide which, and how a key is named, when someone asks for it.
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
Rust (`Cargo.toml`), Java (commit the wrapper),
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

- **Stop reading `task_profiles:` / `escalation:` in `models_list.yaml`.**
  Since 0.1.20 they have their own files; the old sections are still read
  with a warning. Remove that path (and the tests that use the old layout
  through `write_model_files`) a version or two later.
- **A configuration error prints a resume hint, then the banner, and is
  logged as a run.** The same run printed the model-file error, then
  "Continue with: certo --resume --project leap" (there was nothing to
  resume), then the banner. Seen again in 0.1.20 with `--auto-model` and
  no model files, which also created `.certo/` in the current folder with
  a `RUNS.md` entry saying "Model: ollama/qwen3.8:27b (picked by
  --auto-model)", although nothing was picked or run. Print the error
  alone, after the banner or instead of it, and write nothing.
- **The `--resume` hint ignores `CERTO_PROJECTS_DIR` from the
  environment.** It prints `certo --resume --project NAME`, which then
  looks in the default projects folder. Print the setting too when it
  isn't the default.
- **`--model` alone fails when no model is configured.** `certo TASK
  --model X` with no `CERTO_LLM_MODEL` anywhere stops with "CERTO_LLM_MODEL
  is required": `load_config()` validates before `override_llm()` applies
  the flags. Same for a local `--base-url` with no key. Found 2026-10-19
  writing `examples/compare-models.sh.example`, which works around it by
  setting the variables. Done when the flags alone are enough.
- **The server tests leak into the current folder and read its `.env`.**
  Run from any folder, `tests/test_server.py` creates
  `projects/acme-website`, `delete-me` and `keep-me` there (found
  2026-10-19 in the repo's own `projects/`). And 4 tests (`test_health`,
  the two unknown-id 404s, `delete_tasks_by_project_unknown_project`)
  fail without a `CERTO_LLM_MODEL` in `./.env`. CI skips them (no
  `server` extra), so only a developer with the extra and no `.env` sees
  it. Give the server fixture its own config and a `tmp_path` projects
  dir.
- **Third-party skills: narrow license detection, `SKILL.md` only.** Eight
  permissive licenses are recognised; anything else is `unknown` and needs
  acknowledgement. Legacy single-file upstream skills can't be installed.
  Fine for now; revisit if people use the feature.
