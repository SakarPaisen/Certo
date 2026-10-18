# Roadmap & Status

Internal planning memory: what's implemented, what's left, known limitations,
and why key decisions were made. This is **not** user docs — see `docs/`
for how to actually use the harness, and `docs/SPEC.md` for the original
build plan.

> **Maintenance note:** update this file whenever milestone status changes, an
> optional feature is built or explicitly deferred, or a new limitation is
> discovered. Keep entries terse — outcome + one-line why. See `CLAUDE.md`.
>
> **Full history:** every decision below is a compressed summary. The
> complete narrative — alternatives considered, live-verification
> transcripts, exact quotes — for every entry through 2026-09-20 lives in
> `docs/ROADMAP.txt` (a frozen snapshot, not maintained further) and in git
> history. If a compressed entry here is missing detail you need, check
> there before re-deriving it from scratch.

## Milestone status (docs/SPEC.md section 11)

| # | Milestone | Status |
|---|---|---|
| 1 | Scaffold + config | Done |
| 2 | llm/tools/agent/runner + hello-world e2e | Done, verified live |
| 3 | Provider-swap live proof | **Unblocked, not run** — a local model (Ollama) and cloud keys are configured since 2026-10-17; run one task with two `CERTO_LLM_MODEL` values to close it |
| 4 | Custom tool + test | Done — `run_tests_tool` |
| 5 | CLI + README + execution-mode flag | Done, verified live |
| 6 | Optional (section 9) | Docker execution: done. Server mode: done (REST async submit+poll, WS streaming, OpenAI-compatible `/v1/chat/completions`). Skills: done — shared catalog + per-project AGENTS.md. Every section-9 item is done. |

## Backlog — optional / not yet built

- **ECS/EC2 execution backends** — `workspace.py`'s `build_workspace()` is
  the single dispatch point; adding one is a new branch, not a rewrite.
- **`run_tests`/verification generalization still not fully generic.**
  Covers Python/Node/Go/Rust/Java. Not done: a JS project's actual test
  runner (jest/vitest/etc.) isn't config-parsed, only a defined
  `scripts.test` is run as opaque; no Python lint/typecheck beyond
  ruff/mypy; no JS/TS lint-tool inference from config (see next item); no
  ecosystem beyond these six; Java verification is detection-only here and
  in the Docker image (no Maven/Gradle toolchain in either).
- **Milestone 3 live provider-swap proof** — no longer blocked (a local
  Ollama model and cloud keys exist since 2026-10-17); not run yet.
- **Third-party skills: narrow license detection, `SKILL.md`-only.** The
  license text heuristic covers 8 permissive licenses. Everything else is
  `unknown` and needs explicit acknowledgement. Legacy single-file `.md`
  upstream skills can't be installed. The automated tests mock the SDK
  fetch. Verified live against `anthropics/skills` @ `8a1541c`:
  - `frontend-design` refused (collides with the hand-placed copy).
  - `algorithmic-art` detected as Apache-2.0.
  - `pdf` came out `unknown` (proprietary), and `enable` refused it
    without `--accept-unknown-license`.
  - The agent received `algorithmic-art` only once it was enabled.
  - A tampered copy was skipped, and `sync` restored it.
  - A hand-edited lock enabling `pdf` without acknowledgement was skipped,
    and an untracked directory was ignored.
- **JS/TS lint tools aren't auto-detected from config** — a Node project's
  own `scripts.lint`/`scripts.typecheck` *are* run if defined, but there's
  no ESLint/tsconfig-based inference the way `_ruff_configured()` infers
  Python lint relevance with no named script (ESLint config formats/flat-config
  variants make this a harder question than the ruff/mypy case).
- **Docker execution from a pip install** — `workspace.py` builds the
  agent-server image from `docker/agent-server.Dockerfile` with the repo
  root as context (`_REPO_ROOT` is computed from `__file__`). From an
  installed wheel that path is `site-packages/..`, and neither the
  Dockerfile nor `src/` is there, so a first Docker run fails unless the
  image was already built from a checkout. Options: ship the Dockerfile
  and tool source as package data and build from a temp context, or
  publish a prebuilt image. Undecided; documented in
  `docs/guides/run-in-docker.md` and in `docs/README.md`'s "Known
  limitations".
- **Benchmark strategies beyond `single` and `escalate`** — `best_of` (N
  attempts, the verifier picks) is the planned next entry in
  `bench_strategies.STRATEGIES`. Each must be benchmarked on a local and a
  cloud model before release (CLAUDE.md working agreements).
- **`bench.yaml.example` isn't in the wheel** — it is in the sdist
  allowlist only (repo root), while the model examples moved into
  `src/certo/examples/` in 0.1.10. A pip user has to download it
  (`docs/guides/write-a-benchmark-file.md` gives the URL). Fix: ship it in
  `certo/examples/` and name the `cp` command when `bench.yaml` is
  missing, as `model_files.missing_message()` does. Not done on
  2026-10-18 because a benchmark was running from the checkout.
- **Bench estimates from recorded cost, not a token guess** — the plan
  prices every run at a fixed ~500k input / ~20k output tokens. Since
  0.1.13 each results folder's `cost.json` holds each model's real average
  cost per run; the plan could use that (same model id, from earlier
  results in the same parent folder) and fall back to the guess only for
  models with no history, as the "likely" figure already does for climb
  rates. Not built.
- **Move task profiles and escalation ladders out of `models_list.yaml`**
  (user's idea, 2026-10-17; not started). The list would hold only what
  models exist (ids, ratings, descriptions: shared catalog data); a new
  optional `model_policy.yaml` would hold how to choose among them
  (`task_profiles:` and `escalation:`), the part most likely to differ per
  project. One file for both, not two: `--auto-model` and `--escalate`
  are two answers to the same question, and users already handle four
  files. Same lookup as the others (`CERTO_MODEL_POLICY_FILE`, project
  folder, user folder; first found used whole), shipped only as
  `model_policy.yaml.example`. Unlike the list, a missing file is not an
  error: built-in defaults (derived ladder, a `default` profile).
  Migration: keep reading the sections from `models_list.yaml` for a
  version or two with a warning naming what to move (cheaper than the
  0.1.10 hard error, and the old layout isn't wrong, only out of date).
  `catalog_check` validates ladder names across the two files; `bench.yaml`
  gains `model_policy_file` for symmetry. Feature bump; docs: models-yaml
  reference, both model guides, the auto-model/escalation concept page.
- **Escalation: restart a rung from a clean workspace** — only "continue in
  the same files" exists. `_stream_escalation` takes the workspace listing
  before each rung, so a "restart" mode (copy the original files back
  before the next rung) is one more branch there; not built.
- **Escalation ran live but never climbed** — the 0.1.13 baseline
  (`docs/benchmark/baseline-0.1.13.md`, 2026-10-17) had an explicit and a
  derived ladder arm (qwen3.8-27b-local first); all 18 runs ended on rung
  1, so no climb, handoff or derived-ladder ordering was measured. Needs
  harder tasks (task set v2). Escalation under Docker is covered by
  fake-workspace tests only, not a real container.
- **Benchmark baseline: 0.1.13 only, 1 repeat** —
  `docs/benchmark/baseline-0.1.13.md`: local qwen3.8-27b and cloud
  claude-sonnet-5-5 both 9/9, one fooled run (led to `unchanged`, 0.1.14).
  The 9 tasks don't separate the models; 0.1.14's `unchanged` and 0.1.15's
  transcripts are not benchmarked yet.
- **Node "no tests" counts as verified** (found by `certo bench`'s first
  integration run, 2026-10-16): `node --test` exits 0 when it finds no test
  files, so `npm test` passes and the verdict is `verified` for a project
  with no tests. The same holds for any runner that exits 0 on nothing to
  run. Documented in `docs/reference/verification-by-language.md`; the
  benchmark counts it as "fooled". Not fixed.
- **Bugs found while writing `docs/` (2026-10-16), not fixed yet:**
  - `cargo clippy` is planned unconditionally whenever `cargo` exists, so a
    toolchain without the clippy component makes a Rust project `failed`
    (`error: no such command: clippy`, exit 101) instead of `unavailable`.
    Reproduced with a `cargo` shim. Workaround documented in
    `docs/troubleshooting.md`: `rustup component add clippy`.
  - `WS /tasks/stream` and `/v1/chat/completions` call `stream_task`
    without `run_id`/`project`, so with `CERTO_ARTIFACTS_DIR` set their
    records land under `_unscoped/<new uuid>` even when a `project` was
    sent. Only `POST /tasks` files them under the project and task id.
  - `llm_check.explain()` always says "in .env" (e.g. "Check
    CERTO_LLM_API_KEY in .env"), although since 0.1.5 the value usually
    comes from the user settings file or the environment.
- **`/v1/chat/completions` doesn't surface `verification_state`** — its wire
  format has no natural field for it; a caller using only that adapter gets
  the agent's final text with no independent verification signal.

## Backlog — growth (proposed 2026-10-17, not started)

Goal: people use Certo for complex, multi-language apps and trust its
verdicts. The pitch is the name: Certo checks the work, and can say how
often it would have been fooled. Every quality item is judged by `certo
bench` on a local and a cloud model (working agreements 2 and 3). Order
inside each group is the suggested priority; suggested overall start:
bench task set v2, milestone mode, independent spec tests, GitHub Action.

**1. Prove it publicly**
- **Published benchmark results per release** —
  `docs/benchmark/baseline-<version>.md` (local vs cloud, fooled rate,
  cost per solved task) and a README badge. The first one exists
  (0.1.13); the badge and one per release don't.
- **Bench task set v2: app-scale tasks** — today's 9 are small and mostly
  single-file. Add multi-file, multi-language ones: Go REST API with a
  database, React frontend + API, Rust CLI with subcommands, a fix inside
  an existing mid-size repo. Bump the task-set `VERSION`; results stay
  comparable only within one version.
- **Pull-request CI workflow with a ruff gate** — only `release.yml`
  exists, and `main` has lint/format findings to clear first.

**2. Complex tasks**
- **Milestone mode** — split a big task into milestones, each with its own
  acceptance checks; run and verify them one at a time, building on
  `--resume`/`STATUS.md`. The main step from "small task" to "app".
- **Independent acceptance tests from the spec** — before building, a
  separate conversation (optionally another model) writes tests from the
  task text only; the builder may not edit them. Brings the benchmark's
  hidden-test idea to real runs (the agent's own tests share its
  misunderstandings: Hanoi, Wordle).
- **Context management for long runs** — the SDK's own conversation
  condensing (verify-first, golden rule 1), plus a warning when a local
  model's context window is too small for the task (qwen3.8 at 32K).
- **Checkpoints and rollback** — a git snapshot per fix attempt and per
  escalation rung, so a bad attempt can be undone; also the basis for the
  escalation "restart" mode above.

**3. Languages and frameworks**
- **Run-the-app verification** — start a server and probe an HTTP
  endpoint; build a frontend and load it in a headless browser (the SDK
  ships a browser tool) for a blank page or console errors. The web
  counterpart of the entry-point smoke run.
- **Close the existing verification gaps** — jest/vitest, ESLint/`tsc`
  inference, the clippy bug, Node "no tests" = verified, a Maven/Gradle
  toolchain in the Docker image (all listed above).
- **New ecosystems** — in order: C#/.NET, PHP (Composer), Ruby, Kotlin/
  Android (Gradle), C/C++ (CMake), Swift.
- **Framework skills with verification recipes** — listed in "Backlog —
  built-in skills to make" below.

**4. Adoption**
- **GitHub Action** — an issue labelled `certo` becomes a pull request
  with the verdict and checks in its description. Likely the strongest
  adoption lever.
- **MCP server** — so Claude Desktop, Cursor, Zed and similar can call
  Certo as a tool and get the verdict back (the OpenAI-compatible endpoint
  can't carry it).
- **Run report** — an HTML/Markdown summary per run: what changed, which
  checks ran, cost, why the verdict. Built from the existing artifacts.
- **Live progress view** in the terminal: current milestone, last check,
  cost so far.
- **Prebuilt Docker image** — fixes "Docker execution from a pip install"
  above and makes the safe mode one command.
- **`certo init models`: a setup helper for the model files** — `certo
  init` covers one model (.env, Ollama model list, tool-call check), but
  nothing helps with `models_list.yaml`/`models.yaml`, the heavy part of
  using `--escalate`/`--auto-model`. Same style as `certo init` (a few
  questions on a terminal, none without one, a real check at the end):
  find provider keys in the environment or `.env` and the models on the
  Ollama server; copy `models_list.yaml.example` to the user folder if
  there is no list; offer the catalog entries the user can actually run
  (an Ollama model not in the list gets "add it first", never invented
  ratings); write `models.yaml`, a key from an environment variable as
  `${VAR}`, never copied (verify first that `models.yaml` expands
  `${VAR}`; add it if not); test each model with the `check --models`
  tool-call check and deactivate failures, saying why; print the ladder
  `--escalate` would use. The first-run path must still need no model
  files: this is the second step, for escalation.
- **`certo models update`** — compare the shipped example catalog with the
  user's `models_list.yaml` (new models, changed ratings) and offer to
  merge, since a release never touches the user's copy and keeping it
  current is manual today.
- **Docs website and gallery** — `docs/` is plain Markdown with no site
  generator; add a site, a gallery of apps built with Certo (verdict and
  cost each), and a short demo video.

**5. Best harness for local models**
- **Per-tier tuning** — shorter prompts and stricter tool-call repair for
  small models, gated by model tier and measured on both tiers.
- **`certo doctor` for Ollama** — model pulled, context size, thinking
  mode, measured tokens per second.
- **Measured speed and context in the catalog** — filled from real runs,
  not guessed, so ladders can weigh speed (the "fastest of the cheapest"
  question; today's ratings have no speed data, and a `speed` rating
  would count as capability).

## Backlog — built-in skills to make (proposed 2026-10-17, not started)

The running list of **skills** to add to `src/certo/builtin_skills/`
(shipped in the wheel, loaded for every run). Today there are 12: eight
`lifecycle/` skills, `git/commit-conventions`, `python-web/fastapi-
conventions` and `pin-dependencies`, `testing/pytest-conventions`. Add new
skill ideas here; move an entry to "What's implemented" when it ships.

**Rules for every new skill:**
- **Short, narrowly triggered.** Every skill that fires costs prompt
  context, which a local model with a 32K window can't spare, and the
  lifecycle triggers are already broad ("add", "build", "test", "error").
  Prefer `paths:` triggers (fire when the agent touches a file such as
  `go.mod`) over keywords.
- **Measured.** Each is checked with `certo bench` on a local and a cloud
  model before release (working agreements 2 and 3): a skill that seems
  helpful but crowds out the task is a net loss.
- **Authored for Certo, not downloaded,** where it states Certo's own
  checks (the lifecycle-skills decision); legacy `triggers:`/`paths:`
  format so they really trigger.

**1. Skills that make a project verifiable** (Certo-specific; first)
- **`testable-interactive-apps`** — keep logic apart from input/output so
  games and menus are testable without a terminal. Triggers: game,
  interactive, menu, terminal. Targets the starter tasks (Wordle,
  Asteroids) and the Hanoi case (#8).
- **`python-environment`** — use the project's own `.venv`; never install
  into Certo's interpreter or with `pip install --user`; declare a
  dependency in `pyproject.toml` before using it. The agent-side half of
  "confident but wrong" #9.
- **`node-project-setup`** — a real `test` script with at least one test
  (`node --test` or vitest), a `build` script, a committed lockfile, no
  interactive scaffolders (`npm create vite` with flags). Covers "Node
  with no tests counts as verified" and #2, #4.
- **`cli-entry-points`** — `__main__` guard last, a closed stdin doesn't
  hang, `--help` and non-interactive flags work, so the smoke run can
  start the program (#8).
- **`test-oracles`** — derive expected values independently, never by
  copying the implementation's output; check a suspicious test against
  its own setup before re-editing correct code (#7). May become a section
  of `lifecycle/testing-and-verification` instead of its own skill.

Suggested first three: `testable-interactive-apps`, `python-environment`,
`node-project-setup` (each targets a recorded failure, and the bench's
game and Node tasks can measure it).

**2. Language skills** (path-triggered; one per ecosystem Certo verifies)
Each says how to set the project up so Certo's checks for that language
(`docs/reference/verification-by-language.md`) find it and pass.
- **Go** (`go.mod`) — `go test ./...`, `go vet`, table-driven tests.
- **Rust** (`Cargo.toml`) — `cargo test`, clippy, and the missing
  clippy component gotcha.
- **Java** (`pom.xml`, `build.gradle`) — commit the Maven/Gradle wrapper:
  without a toolchain Certo can't verify.
- **TypeScript** (`tsconfig.json`) — strict mode, `tsc --noEmit` as a
  `typecheck` script (Certo runs it when defined).
- **Python** — extend `pytest-conventions` with ruff/mypy setup in
  `pyproject.toml` (Certo runs them when installed in the project env).
- New ecosystems from the growth backlog (C#/.NET, PHP, Ruby, Kotlin,
  C/C++, Swift) each get a skill when their verification lands.

**3. Framework skills** (each with a verification recipe: how to build,
test and smoke-check an app of that kind)
- **Web frontend: Vite/React** — build, a test runner, a smoke test.
- **Next.js**, **Express**.
- **Django**; **FastAPI** — extend the existing `fastapi-conventions`
  with its verification recipe.
- **Spring**, **Rails**, **Laravel**.

**4. App building blocks**
- **`http-api-testing`** — the framework's test client, no real network
  in tests.
- **`database-basics`** — SQLite for small apps, migrations, an isolated
  test database.

## Moved

- Module notes and internal limitations: `ARCHITECTURE.md`.
- The decisions log: `DECISIONS.md`.
