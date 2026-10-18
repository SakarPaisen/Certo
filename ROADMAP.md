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

## What's implemented

Per-module reference. See `docs/` for user-facing behavior; see the
decisions log below for *why* a given design was chosen.

- **`config.py`** — env parsing, model-agnostic (`CERTO_LLM_MODEL` prefix selects
  provider). `override_llm(cfg, model=, api_key=, base_url=,
  reasoning_effort=)` is the per-request override mechanism shared by
  `cli.py`/`server.py`. `resolve_project_dir(projects_dir, project)` is the
  shared resolver both `--project` and the server's `project` field go
  through: rejects an absolute/`..`-containing name outright, then rejects a
  symlink-resolved (`os.path.realpath`) path that escapes `projects_dir` —
  closes a real path-escape bug (`os.path.join` silently discards the first
  arg when the second is absolute). `max_task_seconds` (`CERTO_MAX_TASK_SECONDS`,
  default `1800`) is the task-level wall-clock budget `runner.py` enforces
  across every phase. `interactive` (`CERTO_INTERACTIVE`) opts into the
  initial-run interactive checkpoint and drops `_AUTONOMOUS_SUFFIX`.
  `load_settings_files()` fills `os.environ` from `./.env`, then the user
  file (`user_settings_path()`: `$XDG_CONFIG_HOME/certo/.env`, else
  `~/.config/certo/.env`), and returns each variable's `SettingSource`;
  `load_config()` calls it when no `env` mapping is passed.
  `no_worktree_warning` (`CERTO_NO_WORKTREE_WARNING`) silences `worktree.py`.
- **`acceptance.py`** — optional, caller-supplied machine-checkable
  acceptance criteria, scoped to `file_exists`/`file_contains` only (no
  command-exec kind — see decisions log). Own path-containment check
  (mirrors `resolve_project_dir`'s logic, separate implementation). 1MB read
  cap on `file_contains`. Wired via a new `"acceptance_failed"` terminal
  state, applied once at the very end of `stream_task`, downgrading what
  would otherwise be `"verified"` only.
- **`llm.py` / `tools.py` / `agent.py`** — SDK wiring; default preset tools +
  `run_tests`. `build_llm()` passes `reasoning_effort` through when set;
  `none`/`off` (config folds `off` into `none`) and an unset Ollama model
  pass an explicit `None` (no reasoning param sent); any other unset model
  omits the kwarg so the SDK's own `"high"` default applies. `AgentContext.system_message_suffix` carries five
  behavioral policies: `_AUTONOMOUS_SUFFIX` (omitted when `cfg.interactive`),
  `_README_SUFFIX` (leave a real `README.md`), `_NONINTERACTIVE_TOOLING_SUFFIX`
  (use CI/non-interactive flags, don't blindly retry a no-op command),
  `_VERIFY_BEFORE_FINISH_SUFFIX` (run tests before claiming success), and
  `_LIFECYCLE_SKILLS_SUFFIX` (apply lifecycle-skill discipline even
  off-trigger, skip for trivial changes, never substitute for actually
  verifying). `build_agent()`/`build_llm()` take an optional `usage_id` so
  auto model selection's candidates each get a distinct SDK LLM-registry key.
- **`runner.py`** — `stream_task()`/`run_task()` are the core primitives;
  wires `cfg.max_iterations` into `Conversation(max_iteration_per_run=...)`
  (previously unset, silently defaulting to the SDK's `500`). Both return a
  `TaskOutcome` — a bounded verification verdict (`VERIFICATION_STATES`) from
  `_verify_and_report()` (harness-side, no-LLM re-run of the project's own
  checks; doesn't trust the agent's self-report), checking
  `conversation.state.execution_status` for `STUCK`/`ERROR` before verifying
  and after every retry. `_enforce_task_tracker_completion()` runs first: if
  the most recent `task_tracker` observation shows unresolved items, resends
  a follow-up and retries (bounded by `CERTO_MAX_VERIFY_RETRIES`); an
  unresolved list becomes a terminal `"incomplete"` state, short-circuiting
  verification entirely (an unused or already-`done` tracker is not a
  violation). `CERTO_CONFIRM_MODE=always` is wired via
  `_run_with_confirmation()`, wrapping every `conversation.run()` call site
  and returning `"ok"`/`"confirmation_required"`/`"budget_exhausted"`; no
  `on_confirm` handler (server mode) rejects the pending action once and
  stops rather than auto-approving or hanging. `CERTO_MAX_TASK_SECONDS` is
  checked before every `.run()` call across all three call sites. `CERTO_INTERACTIVE`
  wires an `OnAwaitingInput` checkpoint around the *initial* run only (`cli.py`
  supplies a terminal handler, `server.py` doesn't); the deadline is paused,
  not spent, while waiting on a human reply. `CERTO_MODEL_SELECTION=auto`
  wires a `ModelChain` (see `model_selection.py`) with automatic fallback on
  a `ConversationRunError` wrapping the SDK's own `LLMError` hierarchy;
  `write_model_decisions()`/artifact-writing both run in a `finally` block
  around the whole task so they still fire when every candidate fails.
  `CERTO_ARTIFACTS_DIR` mints a `run_id` (or uses the caller's, e.g.
  `server.py`'s `TaskRecord.id`) and writes `metadata.json`/`transcript.json`/
  `metrics.json` via `artifacts.py`.
- **`custom_tools/run_tests_tool.py`** — language-neutral verification in
  four stages: **detection** (`detect_project()` — Python/Node/Go/Rust/
  Java-Maven/Java-Gradle marker walk, plus an `"ambiguous"` state for
  monorepos with sibling manifests at the same shallowest depth), **plan
  discovery** (`discover_verification_plan()`, pure), **execution**
  (`execute_check()`, the only subprocess-spawning stage; `stdin=DEVNULL` by
  default on every check), and **aggregation** (`VerificationRun.state`,
  which a secondary check can only ever pull down from `verified`, never
  promote up to it). `CheckOutcome.status` is a five-value enum
  (`passed`/`failed`/`skipped`/`unavailable`/`timed_out`) so "should be
  checkable but isn't" (missing toolchain) is never confused with "not
  configured" or "ran, nothing to check." `CheckSpec.precomputed` supports a
  pure, no-subprocess static check — used by `entrypoint-ordering`, an
  AST-based check (recursive discovery, root always included) that a Python
  entry point's `if __name__ == "__main__":` guard is its last top-level
  statement. The agent-facing `run_tests` tool keeps its original rich
  Python/Node contract and reuses stages 1–3 for Go/Rust/Java. Python adds
  a setup stage, `prepare_python_env()`: find or create the project
  environment, probe which of pytest/ruff/mypy it can import, and install
  pytest into it when tests exist but pytest doesn't. Planning stays
  subprocess-free by reading that result. Every check runs through a
  `CommandRunner` (`execute_check(..., runner=)`). `CheckSpec.env` holds
  extra variables only, never a copy of `os.environ`. Java is
  detection-only in this dev environment and the Docker image (neither ships
  a Maven/Gradle toolchain).
- **`cli.py`** — `python -m certo "<task>" [--execution] [--project]
  [--agents-md] [--model] [--api-key] [--base-url] [--reasoning-effort]
  [--interactive] [--require-verification] [--acceptance-checks]
  [--auto-model]`, plus `certo verify [PATH] [--require-verification]`
  (`verify_main()`: `run_full_verification` with no agent/LLM, same verdict
  line and `_FAILING_STATES` exit codes). `task` resolves via `resolve_task_source()` (http(s) URL,
  then existing local file, then literal text — CLI-only). `--require-verification`
  makes an `inconclusive` result exit nonzero too (default behavior
  unchanged otherwise). `--auto-model` sets `cfg.model_selection="auto"`;
  prompts for a choice only when `--interactive` is also set. Before
  `run_task` it prints `worktree.worktree_warning()` to stderr, unless
  silenced or the `--project` folder is one Certo created.
- **`worktree.py`** — stdlib only. `worktree_warning(path)`: None for an
  empty folder or a clean repository, a warning for uncommitted changes
  under `path` (`git status --porcelain -- .`, untracked included), a note
  outside git. `record_created_project`/`was_created_by_certo` keep
  `CERTO_PROJECTS_DIR/.certo-created-projects`, one name per line.
- **`model_catalog.py`** — pure data/scoring for `models.yaml`, no SDK
  imports: `load_model_catalog()`, `classify_task()` (keyword triggers, same
  pattern as skills), `score_entry`/`rank_candidates` (weighted sum over a
  profile's declared axes, skips `activated: false` entries entirely).
- **`model_selection.py`** — the SDK-touching layer: `ModelChain` is a
  forward-only cursor over one task's ranked candidates (scored once, never
  re-scored mid-task), `.advance()` logs a `ModelDecisionRecord` (never
  carries secrets). `config_for_entry()` passes `""` (not `None`) for an
  unset field so a keyless local model can't inherit a stale API key.
  `write_model_decisions()` rewrites `MODEL_DECISIONS.md` from the full list
  every time (never appends).
- **`artifacts.py`** — pure file-writing for `CERTO_ARTIFACTS_DIR`:
  `<artifacts_dir>/<project-or-"_unscoped">/<run_id>/`, own path-containment
  check. No SDK dependency. A sibling top-level directory (mirrors
  `CERTO_PROJECTS_DIR`'s shape), not nested inside a project.
- **`bench_tasks.py` / `bench_config.py` / `bench_strategies.py` /
  `bench.py` / `bench_report.py`** — `certo bench`. The task set ships in
  `src/certo/benchmark_tasks/` (`VERSION` file; 9 tasks, each `task.md`,
  optional `starter/`, `hidden_tests/`, `reference/`). `grade()` copies the
  hidden tests into `.certo_hidden_tests/` and runs them in the project's
  own environment (pytest with its own ini and `PYTHONPATH=workspace`;
  `node --test`). `bench_config.py` validates `bench.yaml` against
  `models.yaml` names; `bench_strategies.STRATEGIES` is the registry
  (`single`, `escalate`), each strategy building an explicit `Config` from the
  catalog entry (`run_config`, Certo defaults, isolated skill dirs, no
  `.env`). `bench.py` runs repeat-major, one JSON per run (atomic write),
  workspace snapshots, `--max-cost`, `--parallel` (cloud-only),
  `--resume` (fingerprint + task-set hash must match), each run's
  conversation in `runs/transcripts/<run_id>.json` (0.1.15). `bench_report.py`
  renders `results.md`/`results.csv` from the folder alone. The task
  prompt is passed to `stream_task`, not copied into the workspace, so an
  empty-starter Python task keeps the normal "empty folder + task names
  Python → environment up front" behaviour.
- **`model_files.py`** — where `models_list.yaml` and `models.yaml` are
  found (0.1.10): an explicit setting (`CERTO_MODELS_LIST_FILE` /
  `CERTO_MODELS_FILE`, or `models_list_file` / `models_file` in a bench
  file), else the current folder, else the user settings folder; first
  found wins, per file. `missing_message()` prints the `cp` command for
  the shipped example in `certo/examples/`. `model_catalog.load_model_catalog
  (list_path, models_path)` merges the two into the same `ModelCatalog`
  as before (entries gain `configured`), so ranking, ladders and checks
  are unchanged; a model only in the list is `configured=False,
  activated=False`.
- **`catalog_check.py` / `escalation.py` / `catalog_report.py` /
  `model_pricing.py`** — escalation (0.1.9). `model_catalog.py` parses
  the optional `escalation:` section (`EscalationSettings`, `Ladder`,
  `LadderRung`) and gained `capability()` (score without the cost axis).
  `catalog_check.check_catalog` is the one consistency check (errors and
  warnings as plain sentences); `load_checked_catalog` is how
  `--auto-model`, `--escalate` and `certo bench` load the file.
  `escalation.py` (pure) resolves a `ResolvedLadder` (explicit, or derived
  from the ratings), defines `ESCALATING_VERDICTS`, `RungResult`, the
  before/after `workspace_listing`/`FileChanges` and `handoff_message`.
  `runner._stream_escalation` is the loop: one fresh `Conversation` per
  rung in the same workspace, reusing `_run_stream_task_phases` and
  `_apply_acceptance_checks`; `TaskOutcome.rungs`/`final_rung`.
  `catalog_report.py` is `certo check`'s catalog part and `--models`.
  `model_pricing.py` holds `is_local`/`estimate_run_cost` (moved from
  `bench.py`). `bench_strategies.EscalateStrategy` is `strategy: escalate`.
- **`project_state.py`** + `certo --resume` — stdlib only. The CLI
  passes `save_state=True` (`CERTO_SAVE_STATE`, default on) to
  `stream_task`, which then builds the `Conversation` with
  `persistence_dir=<workspace>/.certo/conversations` and its own
  `conversation_id` (local runs only: the SDK raises for a remote one) and
  keeps `run.json`/`STATUS.md` current via `_ProjectStateWriter` (start,
  each verification pass through a new `on_verification` hook, the final
  outcome after acceptance checks, or `interrupted`/`error` from the
  `finally`). `--resume` loads `run.json`, reopens the same conversation
  id (the SDK's `ConversationState.create` resumes it; tools may only be
  added, everything else, LLM included, may change) and sends
  `resume_message()` as the first message while `task` stays the goal for
  verification. When the conversation can't be reopened (Docker, folder
  gone, SDK refuses), a fresh conversation gets the task and `STATUS.md`
  instead. Server and bench never pass `save_state`.
- **`run_summary.py`** — pure: `summarize_run(duration, {usage_id:
  Metrics.get()})` → `RunSummary` (wall-clock time, models that actually
  made calls, tokens, cost; zero cost with nonzero tokens = "unknown",
  not free, except for a local-prefix model id, which is free). Built in `stream_task`'s `finally` on every run, attached to
  `TaskOutcome.run_summary`, printed by `cli.py`, written to
  `metadata.json`/`metrics.json`.
- **`llm_check.py`** + `certo-admin check-llm` — one direct
  `LLM.completion()` built via `build_llm()` (same config path as a real
  run), `num_retries=0` plus a short timeout, pass = non-empty text.
  Construction happens inside the try, since the SDK validates at build
  time. Errors are classified, with the API key scrubbed.
  `check_tool_calling()` is the variant behind `certo init`/`certo check`:
  the same build, but sent through the SDK's `make_llm_completion` with
  `FinishTool`, passing only on a tool call; `explain()` turns a result
  into one plain sentence with the fix.
- **`init_cmd.py`** — `certo init [FOLDER]` and `certo check`. Questions
  go through an injectable `Prompter`; `gather_settings()` returns
  `Settings` (key never in its repr) or `None` (no terminal, no flags:
  every preset commented out). `render_env()` writes the chosen lines
  plus the other providers' presets, to the user file
  (`write_user_settings`) or `FOLDER/.env`, as the scope question
  (`--global`/`--local`) decides. `check_main()` prints
  `print_setting_sources()` before `run_check()`. Package data in
  `src/certo/starter/`: `providers.toml` (menu order, default models),
  the workspace `README.md`, `gitignore`, and `tasks/wordle.md`/
  `asteroids.md`.
- **`project_env.py`** — each Python project's own environment (stdlib
  only, since the Docker image imports it next to `custom_tools`).
  `ensure_project_env()` reuses a `uv.lock` project (through `uv run`), or a
  working `.venv`/`venv`, searching up to the workspace root. Otherwise it
  creates `.venv` with `uv venv --seed`, then plain `uv venv`, then
  `python3 -m venv`; the base interpreter is never `sys.executable`.
  `CREATED_MARKER` lets Certo rebuild only venvs it made. `LocalRunner`
  (host subprocess, stdin closed, Certo's own `bin/` stripped from PATH)
  and `WorkspaceRunner` (the Docker container via
  `workspace.execute_command`, host↔`/workspace` path mapping) are the two
  `CommandRunner`s. `terminal_env()` builds the agent terminal's extra
  variables, and `wants_python_env()` decides about a workspace before the
  agent starts. `runner.py`'s `_prepare_agent_env()` calls it, then passes
  `project_env`/`terminal_env` to `build_agent()`. `tools.py` puts them in
  the terminal `Tool`'s `params` (`env` plus `terminal_type="subprocess"`).
- **`workspace.py`** — `build_workspace(cfg)` single dispatch point;
  `local` returns a path, `docker` returns a `DockerWorkspace`, both context
  managers.
- **`docker/agent-server.Dockerfile`** — layers our tool source onto
  `ghcr.io/openhands/agent-server`.
- **`server.py`** — `GET /health`, `POST /tasks`, `GET /tasks/{id}`,
  `WS /tasks/stream`, `GET /v1/models` + `POST /v1/chat/completions`
  (OpenAI-compatible, streaming and non-streaming). All task-facing
  endpoints share one background-thread+callback pattern. Accepts the same
  per-request LLM overrides as the CLI (the OpenAI adapter uses distinct
  `llm_*`-prefixed fields since `model` is wire-mandated and echo-only).
  `require_verification`/`acceptance_checks` are supported on the native
  REST/WS API only — not `/v1/chat/completions`, which never surfaces
  `verification_state` at all. `DELETE /tasks/{id}` and
  `DELETE /tasks?project=NAME` back the task-store persistence feature.
- **`task_store.py`** — pluggable persistence (`CERTO_TASK_STORE`:
  `memory`/`redis`/`sqlite`/`mysql`/`postgres`), one `TaskStore` ABC.
  `sqlite`/`mysql`/`postgres` share one `SQLTaskStore` via SQLAlchemy Core.
  `redis` uses native per-key `EX` expiration instead of a purge sweep.
  `CERTO_TASK_TTL_SECONDS` (default `0` = forever) governs retention;
  `server.py` runs a 60s sweep only when a TTL is configured.
  `build_task_store(cfg)` is the one factory both `server.py` and
  `admin_cli.py` use.
- **`admin_cli.py`** (`certo-admin`) — maintenance CLI talking directly to
  the store, no running server needed: `show`, `delete-task`,
  `delete-project`, `purge [--ttl-seconds N]` (refuses at `<= 0`).
- **`skills.py`** — two mechanisms: `load_first_party_skills()` loads the
  shared, trigger-based catalog into every `AgentContext` — the built-in
  `src/certo/builtin_skills/` (ships in the wheel) merged with the user's
  `CERTO_SKILLS_DIR`, each read by `load_skill_catalog()`;
  `write_project_context()` writes a caller-supplied, per-project
  `AGENTS.md` (requires `AgentContext.load_project_skills=True`, which is
  consumed lazily by `LocalConversation`, not validated by `AgentContext`
  itself — easy to silently omit). The catalog includes eight authored,
  legacy-format (`triggers:`/`paths:`) lifecycle skills under
  `builtin_skills/lifecycle/` — `repository-discovery`, `requirements-analysis`,
  `implementation-planning`, `testing-and-verification`,
  `debugging-and-failure-repair`, `security-review`,
  `documentation-and-operational-readiness`,
  `completion-and-release-readiness` — which supersede an earlier
  downloaded five-skill `SKILL.md` set (see decisions log).
- **`third_party_skills.py`** + `certo-admin skills
  install|list|enable|disable|update|remove|sync` — local-only,
  license-aware third-party `SKILL.md` skills. Files live in gitignored
  `CERTO_THIRD_PARTY_SKILLS_DIR`, one level deep. Provenance lives in a
  JSON lockfile (`CERTO_THIRD_PARTY_SKILLS_LOCK`: repo, path, commit SHA,
  license id or `unknown`, URLs, `sha256-` integrity, enabled/acknowledged
  flags, never content). `build_agent()` appends
  `load_enabled_skills()` after the first-party catalog. That call
  re-checks enabled, license acknowledgement, hash and name collision,
  since `AgentContext` raises on duplicate names. `config.py` rejects a
  third-party dir that overlaps `CERTO_SKILLS_DIR` or the built-in dir, because the
  first-party `rglob("*.md")` would load downloaded files regardless of
  enablement.

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

## Known limitations (internal/architectural — see `docs/` for user-facing ones)

**SDK/tooling gotchas** (re-verify on any SDK upgrade — see CLAUDE.md golden
rule 2):
- **Skill content can execute code.** `invoke_skill` runs
  `render_content_with_commands()` on a skill body, which executes every
  unescaped ``!`cmd` `` in a shell (confirmed live against v1.47.0). A
  `SKILL.md` directory's `.mcp.json` becomes MCP server config unless it is
  loaded with `skip_mcp=True`. `third_party_skills.py` neutralizes both for
  third-party skills. First-party skills are trusted and left as-is.
- `find_skill_md_directories()` only checks direct children of a skills dir
  (`SKILL.md` one level deep), while `find_regular_md_files()` `rglob`s.
  So any `.md` under `CERTO_SKILLS_DIR` loads as a legacy skill.
- `CERTO_MAX_ITERATIONS` was parsed but never wired to `Conversation` until
  caught while adding the verification retry loop — **closed**, with a
  regression test asserting `Conversation(max_iteration_per_run=...)` is
  actually called (confirmed it fails without the fix).
- Spec's original custom-tool template didn't match the installed SDK
  (v1.47.0, now pinned exactly): `ToolDefinition` is subclassed with a
  `create(cls, conv_state, **params)` classmethod, not built via a factory
  returning instances.
- `get_default_tools()` lives at `openhands.tools.preset.default`, not
  re-exported from `openhands.tools.preset`.
- **The terminal's extra environment is `Tool(name="terminal",
  params={"env": {...}})`**, passed to `TerminalTool.create(conv_state,
  env=...)` and merged over the inherited environment by
  `build_terminal_env` (`openhands/tools/terminal/definition.py`, `env.py`,
  `terminal/subprocess_terminal.py`). `sanitized_env` keeps `PATH` and
  `VIRTUAL_ENV`. **Under tmux, `PATH` from `env` is ignored**: the pane
  pool sets it as session environment, but a new window takes `PATH` from
  the tmux client, Certo's own process. Confirmed live on macOS: a marker
  added to Certo's own PATH appeared in the pane, the venv's `bin/` didn't.
  Certo therefore forces `terminal_type="subprocess"` whenever it passes an
  env.
- `file_editor` requires absolute paths; does not resolve relative to the
  workspace.
- The SDK's `LLM(...)` constructor raises `LLMContextWindowTooSmallError`
  when LiteLLM reports a context window under 16K (e.g. `ollama/llama3`).
  This happens at build time, not call time. A direct `completion()` lets
  LiteLLM's `NotFoundError` (unknown model id) through unmapped: it is not
  an `LLMError`.
- `python-dotenv` does not strip a trailing `# comment` from an otherwise-blank value.
- `sys.executable` inside the PyInstaller-frozen Docker image resolves to
  the frozen binary itself, not a Python interpreter (`_python_command()`
  works around this).
- **A `Message`'s `role` does not indicate where its text lives** — an
  `assistant`-role tool-call message has empty `content`; the actual text
  (including the final "finish" message) comes back as a `tool`-role
  message. Caught only by a live run, not by tests built on the same wrong
  assumption. Any future code reading `Message.role` to find "the answer"
  should exclude only `system`/`user`, not filter to `assistant`.

**The "confident but wrong agent" family** — variants found live (plus
one requested proactively), each root-caused and fixed; see `docs/ROADMAP.txt`
for full transcripts if a fix needs revisiting:

1. **Plain-text reply ends a run exactly like `finish`, no error** — the SDK
   sets `FINISHED` whenever the LLM replies with text and no tool call,
   indistinguishable from a real `finish` (confirmed by reading
   `response_dispatch.py`). Confirmed live twice (asked for confirmation
   instead of building; declared 1-of-6 tracker items "done"). Fix:
   `_AUTONOMOUS_SUFFIX`. `CERTO_INTERACTIVE=yes` is the opt-in escape
   hatch. **Status: fix applied, not re-verified live since.**
2. **Agent runs an interactive CLI tool, the prompt silently auto-cancels
   with no TTY, agent doesn't notice and re-runs the identical command** —
   confirmed live (`npm create vite` interactive prompt, 200K+ tokens
   burned re-running it). Fix: `_NONINTERACTIVE_TOOLING_SUFFIX`. **Status:
   applied, not re-verified live.**
3. **Agent called `finish` admitting known failures, with an invented wrong
   diagnosis** — confirmed live (Hanoi: blamed "sequence handling," the file
   actually had a literal `IndentationError` and never parsed). Fix (two,
   since prompt-only looked insufficient): `_VERIFY_BEFORE_FINISH_SUFFIX`
   plus `runner.py`'s harness-side `_verify_tests_and_retry()` (real,
   no-LLM re-run). **Status: both applied; the harness-side fix confirmed
   against the actual broken repro; not re-verified as a full live run.**
4. **Same pattern, non-Python project, pytest-based verification blind to
   it** — a Vite/React JSX parse error; pytest reported "no tests
   collected" as a false pass. Fix: generalized to run `npm run build` for
   a detected Node project. **Status: applied, unit-tested against real
   npm/node subprocesses; not re-verified against the original repro.**
5. **The verification loop couldn't tell "confirmed working" from "found
   nothing to check," and had no visibility into a `STUCK`/`ERROR` run** —
   fixed with the five-state model (`verified`/`failed`/`inconclusive`/
   `retry_exhausted`/`stuck`) and checking `execution_status`. **Status:
   applied, unit-tested with a fake `Conversation` forcing the real SDK's
   `STUCK`/`ERROR` enum values; not re-verified against a real stuck run.**
6. **Every verification concept was implicitly Python/Node-only** — rebuilt
   around the four named stages and the five-value `CheckOutcome.status`
   enum described above, covering Go/Rust/Java. **Status: applied,
   unit-tested per stage plus real-subprocess runs for every toolchain
   installed in this dev environment; not re-verified against a live
   Go/Rust/Java build task end to end.**
7. **Agent repeatedly re-edited already-correct code chasing a wrong test**
   (Hanoi: the test's own state assumption was wrong, not the
   implementation) **and its diagnostic prose degraded into fluent but
   empty text**, which the SDK's `stuck_detection` didn't catch (it only
   flags exact repetition). Fix: (a) lifecycle skills now say to prove a
   test wrong against its own captured state trace before a second
   re-edit; (b) a new `no_progress` terminal state stops the retry loop the
   moment a fix attempt provably changes nothing in the verification
   output. **Status: (b) applied and verified against the actual on-disk
   repro; (a) is prompt-level, not mechanically testable.**
8. **A generated Hanoi program passed every unit test genuinely, but
   crashed the instant a user picked the interactive `SOLVE` option** —
   `solve()` was defined *after* the `__main__` guard, so `import`ing it
   (what the test does) never hit the `NameError` a direct run does
   immediately; pytest structurally cannot see this bug. Fix: a static
   AST `entrypoint-ordering` check plus a `python <entry point>` smoke-run
   (closed stdin) — the smoke-run alone can't reach `SOLVE` itself;
   `entrypoint-ordering` is what actually catches this bug class. **Status:
   applied; verified against the actual repro (entrypoint-ordering fails
   with the precise diagnosis while pytest passes) plus a synthetic
   regression fixture; now also re-verified against a fresh live agent run
   end to end (`test_run_task_catches_entrypoint_ordering_bug_live`,
   `tests/test_runner.py`) — closes the "not yet re-verified live" caveat.**
9. **The harness's own verification depended on the dev environment.**
   Repro: Certo 0.1.0 from `uv tool install certo`, `ollama/qwen3-coder:30b`,
   `certo "Create hello.py that prints hello, plus a pytest test for it"
   --project smoke`. Verification ran pytest with Certo's own interpreter
   (`~/.local/share/uv/tools/certo/bin/python`), which has no pytest. The
   agent then ran `<that python> -m pip install pytest`, an attempt to
   install into Certo's own environment that failed only because there was
   no pip. It then hacked the code around the problem, and the run ended
   `no_progress`. Invisible from the dev venv, where pytest is a dev
   dependency. Fix: `project_env.py`, a per-project environment shared by
   the agent's terminal and verification, with pytest installed into it
   when tests need it, and nothing ever run with or installed into
   `sys.executable`. Plus `scripts/release_check.sh`, which installs the
   built wheel with `uv tool install` and runs `certo verify` on fixtures
   before every release. **Status: applied. Unit-tested, terminal
   resolution checked against the real SDK terminal, and the release check
   passes against a real tool install. The live task is re-run only by
   `release_check.sh --with-llm`.**
10. **A run that changed nothing was `verified`.** Found by the first
   complete `certo bench` (2026-10-17, 0.1.13): the `ladder` arm's
   `inventory-fix` run on `ollama/qwen3.8:27b` ran 4.6 minutes, 117k input
   tokens, and left the workspace byte-for-byte the starter; the starter's
   own tests pass, so Certo said `verified` and the hidden tests failed
   (`ImportError: OutOfStock`). Not known whether the agent stopped early
   or wrote elsewhere: bench kept no transcript. Fix (0.1.14): the
   `unchanged` verdict (`runner._require_a_change`), one follow-up first.
   **Status: applied and unit-tested; not re-run live.**

## Decisions log (why, not just what)

Each entry is the decision plus the load-bearing reason. Full alternatives
considered and live-verification detail: `docs/ROADMAP.txt`.

- **Acceptance criteria: `file_exists`/`file_contains` only, no
  command-exec kind.** An unauthenticated server caller triggering
  harness-run commands would be a strictly worse surface than the agent's
  own gated terminal tool. Own path-containment impl (mirrors
  `resolve_project_dir`, kept separate — different error-message
  contracts). 1MB read cap on `file_contains`. New `"acceptance_failed"`
  state applied once at the end of `stream_task`, not retried, not on
  `/v1/chat/completions` (no field for it there).
- **Global task budget: wall-clock (`CERTO_MAX_TASK_SECONDS`), not
  iteration counting.** The SDK resets its iteration counter on every
  `conversation.run()` call (confirmed in source) and exposes no way to
  read back consumed iterations; event-counting is provably inexact (a
  plain-text finish produces no `ActionEvent`). Checked in
  `_run_with_confirmation()` before every `.run()` call, and once at entry
  to both retry-loop functions. Default `1800`s, on by default (a safety
  backstop, not a behavior fork).
- **`--require-verification`: opt-in, default unchanged.** Flipping the
  default (`inconclusive` exits `0`) would break existing scripts/CI.
  Threaded through CLI + native REST/WS, not `/v1/chat/completions` (no
  `verification_state` field there to act on).
- **`resolve_project_dir()` closed a real security bug**, not just added
  hardening: `os.path.join(a, b)` silently discards `a` when `b` is
  absolute, so `--project /etc/cron.d` (or the same field in an
  unauthenticated `POST /tasks`) redirected the whole workspace to an
  arbitrary host path; `..` had the same effect. Fixed with string-level
  rejection *and* a resolved-path (`realpath`) containment check — the
  second layer is needed because a plain name with no `..` can still be a
  symlink escaping `projects_dir` (verified live with a real symlink).
  Deliberately doesn't defend against a TOCTOU race (no realistic threat
  here).
- **`CERTO_CONFIRM_MODE=always`**: mechanics (`AlwaysConfirm`,
  `get_unmatched_actions`, `reject_pending_actions`) verified against SDK
  source before wiring. `_run_with_confirmation()` wraps all three
  `conversation.run()` call sites. No handler (server mode) rejects once
  and returns a new `"confirmation_required"` state rather than
  auto-approving or looping. Known accepted gap: each resumed `run()` call
  gets a fresh iteration budget from the SDK.
- **Task-tracker completion enforcement reads live `conversation.state.events`,
  not the tool's `TASKS.json`** — confirmed the harness's `Conversation(...)`
  call never enables persistence, so that file is never written in normal
  operation. New `"incomplete"` state short-circuits *before* project
  verification (an unresolved tracker means completion was never
  established). Reuses `cfg.max_verify_retries` rather than a new knob. An
  unused or already-`done` tracker is not a violation.
- **Pinned `openhands-sdk`/`openhands-tools` to `==1.47.0` exactly**, not a
  range — this project's verify-first posture depends on not trusting SDK
  symbols we haven't re-checked; a floating range would silently
  reintroduce that risk on a routine install.
- **Docker execution: custom Dockerfile**, not the SDK's `DockerDevWorkspace`
  (scoped to the SDK's own dev environment) or a raw pass-through
  (`register_tool()` only affects the calling process, not the container's
  separate agent-server process).
- **Server mode: both async submit+poll and WS streaming** — a single
  blocking `POST` forces clients to hold an unbounded connection open. Both
  share one background-thread+callback pattern.
- **Skills: two separate mechanisms, not one "smart" one.** Rejected an
  LLM-based skill picker — the SDK's own `KeywordTrigger`/`PathTrigger`
  matching already does this deterministically for free. Kept the shared
  catalog (reusable expertise) and per-project `AGENTS.md` (one project's
  facts) as genuinely different concerns.
- **CLI `task` stays one positional with content-sniffing** (URL/file/literal),
  deliberately not extended to the server — a CLI user benefits from
  avoiding shell tricks; a REST/WS caller is already writing code and can
  fetch content itself.
- **Per-request LLM override on the OpenAI adapter uses separate
  `llm_model`/`llm_api_key`/`llm_base_url` fields**, not the wire-mandated
  `model` field — a strict client may set `model` to an arbitrary
  non-LiteLLM string. `TaskRequest` uses plain `model`/`api_key`/`base_url`
  directly. Both end in one shared `config.override_llm()`.
- **Autonomous-behavior fixes are `system_message_suffix` policies, not
  `runner.py` control flow** — a control-flow "auto-continue" treats the
  symptom (the run stopped) without the cause (model uncertainty), and
  would likely just loop into another clarifying question.
- **Per-project `README.md` requirement is a prompt instruction
  (`_README_SUFFIX`), not a harness-generated template** — the harness has
  no idea what's about to be built; the agent is the only party that knows.
  No harness-side check that a README was actually written (soft
  instruction, like the autonomous fix).
- **Harness-side test verification was built together with its prompt fix**,
  unlike the other autonomy fixes — this symptom (an invented, plausible
  wrong diagnosis) is the model being factually wrong about its own state,
  which a "please verify" prompt cannot fix; only re-running the code can.
  Reuses the SDK's `send_message()`-then-`run()` re-entry (confirmed this
  resets `FINISHED`/`STUCK` back to `IDLE`) so retries keep prior context.
  Bounded by `CERTO_MAX_VERIFY_RETRIES` (default `2`).
- **Five SDLC skills were downloaded, not authored**, from
  `addyosmani/agent-skills`, per explicit instruction to source real
  content — each renamed (dir + frontmatter) to satisfy the SDK's
  strict-mode validation. **Superseded** by the 8-skill lifecycle set below.
- **`run_tests` v1 generalization: detect pytest vs. Node `npm run build`**,
  not a full test-runner-detection rewrite — `npm run build` catches
  "doesn't compile" bugs a project's actual test runner might not cover,
  with no per-framework parsing needed. Defaults to pytest when neither
  marker is found, to avoid changing behavior for this repo's own tests.
- **Verification loop rework: five-state model + `CompletionContract` +
  `TaskOutcome`/`TaskResult`**, not another incremental patch — needed to
  represent `"inconclusive"` as distinct from `"verified"` (no tests ≠
  proof of correctness) and to aggregate multiple checks. `TaskResult`
  subclasses `list` so every existing caller keeps working unchanged.
  `"failed"` is a transient internal state only, never a final
  `verification_state`. Surfaced through CLI exit codes and server
  TaskRecord/WS, deliberately not `/v1/chat/completions`. Lint/typecheck/
  npm-test are opt-in by project config, never invented; a configured-but-
  not-installed tool is a limitation, not a failure.
- **Language-neutral verification (4 stages + `CheckOutcome` enum)**
  replaces a hardcoded 2-outcome tuple, because "checkable but tool not
  installed" is the *common* case for 3 of 6 languages, not an edge case.
  `timed_out` is a genuinely new terminal state, retried like a failure but
  distinguished from `retry_exhausted` if still timing out after retries.
  Go/Rust/Java got unconditional standard commands only where the
  ecosystem has one true convention; Java has no secondary checks (no one
  standard lint/typecheck tool). Java is honestly detection-only here and
  in the Docker image.
- **Lifecycle skills (8, legacy `triggers:`/`paths:` format) replace the
  earlier 5 downloaded `SKILL.md` skills** — legacy format was required
  because `SKILL.md` has no trigger frontmatter at all (confirmed in
  source: it's always menu-listed, `invoke_skill` is the only access
  path), and a legacy skill with a trigger is *also* still menu-listed, so
  switching cost nothing on discoverability while adding real triggering.
  Content authored fresh, not downloaded, because it states this harness's
  own architecture directly (AGENTS.md mechanism, sibling skill names,
  this project's `TaskOutcome` vocabulary) — no external generic skill
  could state these correctly; the "download, don't invent" rule applies
  to generic reusable expertise, not project-specific facts. Old `SKILL.md`
  dirs for the 4 overlapping names were deleted, not left alongside —
  confirmed live that leaving both caused `load_skill_catalog()`'s
  dict-merge to silently drop the new content. Known limitation:
  `KeywordTrigger` matching is approximate (relevant-but-unworded tasks
  miss the trigger; broad shared words fire incidentally).
- **`no_progress` detection compares structured verification output across
  retries**, not the agent's own message text — no reliable cheap way
  exists to score "does this text still make sense," and output comparison
  also catches a *coherent* agent stuck on an ineffective fix. Fires after
  exactly one no-progress retry (given the default budget of 2, requiring
  two would be nearly vacuous). New terminal state, not folded into
  `retry_exhausted` — "kept changing" and "provably changed nothing" are
  differently-actionable signals.
- **Entry-point checks: both a static AST check and a real smoke-run**
  (user's explicit choice) — static-only misses non-ordering startup
  crashes; smoke-run-only can't see *why* it crashed and (stdin closed)
  can't even reach an interactive branch. Explicitly rejected guessing
  input to drive the interactive session — no general safe way to guess
  what an arbitrary generated program expects. `CheckSpec.precomputed`
  added as a general, reusable extension, not a one-off bypass.
  `stdin=DEVNULL` made the default for every check, closing a latent hang
  risk globally. Entry-point discovery was later made recursive, reusing
  `detect_project()`'s own `_SKIP_DIRS`/depth-limit walk plus one new
  `tests`/`test`-excluding set (a test file's own `__main__` guard isn't
  the program's real entry point).
- **`reasoning_effort` added as a 5th per-request override field**, reusing
  `override_llm()` — the SDK's own field is documented provider-neutral and
  forward-compatible, unlike the other reasoning knobs considered
  (OpenAI-specific, or legacy-Anthropic-only). Deliberately not validated
  against a fixed choice list (the field is intentionally open-ended).
  `build_llm()` only passes it when set, since an explicit `None` would
  silently override the SDK's own `"high"` default.
- **Task-store persistence: pluggable `TaskStore` ABC, 5 backends**, not
  just a TTL purge — scope expanded per user request. SQLAlchemy Core for
  all 3 SQL backends (one shared implementation, upsert via
  try-UPDATE-then-INSERT). Delete-by-project exposed via both REST and CLI
  (different callers need different access). Redis uses native per-key
  TTL, not a purge sweep. `MemoryTaskStore` deep-copies on save/get (a real
  bug self-caught once the coarse lock was replaced by per-backend
  locking). `create_app()` builds the store once at startup — deliberate
  fail-fast over a broken `.env` silently 500ing on first request.
  mysql/postgres verified live against real Docker containers but excluded
  from the automated suite (too heavy a CI requirement); sqlite/redis are
  tested for real.
- **Monorepo ambiguity: new `"ambiguous"` `ProjectDetection` state**,
  fixing a real bug — `detect_project()`'s claimed "shallowest wins" wasn't
  actually true across different DFS branches (`os.walk` fully explores a
  first-visited branch before a shallower sibling). Fixed by grouping
  matches by depth during one walk. The workspace root (depth 0) is always
  returned immediately and never "ambiguous" — an explicit `--project`
  already told the harness what the project is. Resolves to the same
  synthetic `"unavailable"` shape already used for `"unknown"` — no
  `runner.py`/`CompletionContract` changes needed.
- **Interactive mode (`CERTO_INTERACTIVE`): checkpoint wraps only the
  initial run**, not the task_tracker/verify retry loops — the smallest
  change covering the two failure modes already on record, without the
  real design question of how a human reply should interleave with the
  harness's own automated retry follow-ups. `CERTO_MAX_TASK_SECONDS` is
  paused (not spent) while blocked on a human reply. No new suffix added —
  only `_AUTONOMOUS_SUFFIX` is dropped when interactive. Has no effect
  without a caller-supplied callback (`server.py` never supplies one).
- **Deterministic auto model selection (`CERTO_MODEL_SELECTION=auto`)**:
  deterministic weighted scoring, not an LLM router — no extra model call,
  consistent with the earlier skills decision. One static ranked list
  computed once per task, walked forward under failure, never re-scored
  (the resulting caveat — fallback picks next-best-fit, not necessarily
  more capable — is documented, not solved). Real API keys live directly
  in `models.yaml` (gitignored like `.env`). Visibility:
  `MODEL_DECISIONS.md` in the project workspace plus
  `TaskOutcome.model_decisions`. Docker gets the initial pick but not
  mid-task fallback — `RemoteConversation`'s Python client doesn't expose
  `switch_llm` even though the remote agent-server's REST API does;
  documented rather than built against private SDK internals. The
  retriable exception type is the SDK's own `LLMError` hierarchy — took two
  rounds of live verification to find (not `litellm.exceptions.APIError`,
  not `openai.OpenAIError`, both invisible once the SDK wraps LLM-call
  failures itself). `write_model_decisions()` runs in the whole task's
  `finally` block after a live-caught bug: an exhausted fallback chain
  previously raised before the file was ever written.
- **Per-run artifacts directory (`CERTO_ARTIFACTS_DIR`): a separate
  sibling top-level directory**, not nested inside each project — mirrors
  `CERTO_PROJECTS_DIR`'s shape. `conversation.conversation_stats`/
  `usage_to_metrics` (confirmed in SDK source) gives a full per-model
  cost/token breakdown for free, since model-selection candidates already
  have distinct `usage_id`s. `MODEL_DECISIONS.md` stays put (not moved
  here). A run ID is minted by `stream_task` when none is given;
  `server.py` passes its own `TaskRecord.id` instead. A live-caught bug:
  artifact-writing was moved into the same `finally` block as
  `write_model_decisions()` after an exhausted model chain was found to
  raise before anything was written.
- **`models.yaml` gained a per-model `activated` (bool, default `true`)
  field**, filtered in `rank_candidates()` (not at load time, so a
  deactivated entry still gets schema validation and the duplicate-name
  check). Raises a specific error if every model ends up deactivated.
- **Excluded the 3 third-party `SKILL.md` directories** (`frontend-design`/
  `webapp-testing`/`web-artifacts-builder`) via `.gitignore` + `git rm
  --cached` (untracked, not deleted) — each actually carries Apache-2.0,
  not MIT as MANUAL.md had claimed (fixed in the same change). Scoped only
  to the 3 directories with their own `LICENSE.txt` — the lifecycle/git/
  python-web/testing skills are authored for this project.
- **Project renamed ARICode → Certo, deep and final** (supersedes the
  earlier `coding-agent-harness` → ARICode rename, which deliberately
  changed branding only and kept `import certo`/`CERTO_*`/
  `certo-admin`). This one renames the brand (docs, `pyproject.toml`
  name, `server.py` title/`owned_by`, Docker image tag
  `certo/agent-server:local`) and links (GitHub redirects the old repo URL).
  Console scripts are `certo`/`certo-server`/`certo-admin`; the old
  `harness*` aliases were later removed (see the entry below).
  The package moved `src/harness/` → `src/certo/` (`import certo`,
  `python -m certo`, Docker `--import-modules certo.custom_tools` with
  `OH_EXTRA_PYTHON_PATH=/certo_src`); no import shim for `harness` — the
  package was never published, so nothing outside this repo imports it.
  Env vars `HARNESS_*` → `CERTO_*`, all read through `config._read()`:
  a non-blank `CERTO_` value wins, else a non-blank `HARNESS_` value is used
  with one `logging` warning per variable per process. Blank = unset on
  both sides, so blank `CERTO_` lines from a fresh `.env.example` can't
  mask an old setting. Error messages quote the variable actually read.
  Storage names: sqlite default `certo_tasks.db`, table `certo_tasks`,
  Redis prefix `certo:`, mysql/postgres default DB `certo`, LLM `usage_id`
  `certo`/`certo:<model>`, and agent-facing notices say `Certo …:`. Compat
  reads exist only where a user may have data: legacy sqlite default file
  (only when the path is the default), legacy table (used as-is, never
  auto-renamed — that's the operator's call), legacy Redis keys (read
  fallback, migrated on save). No fallback for the DB name: a wrong DB
  fails loudly and the fix is one env var. `usage_id` changes are
  unversioned, since they're only per-run telemetry keys. The
  third-party skills lockfile never carried the old name.
  The GitHub repo is renamed (`alessioricco/certo`) and Certo is on PyPI
  since 0.1.0; `docs/launch/github-rename.md` is the historical checklist. `docs/ROADMAP.txt` is a
  frozen snapshot, so it keeps the old names on purpose.
- **Live entrypoint-ordering/smoke-run test built its own throwaway
  `tmp_path` fixture, not `projects/hanoi/` or anything under `projects/`**
  — that directory is user-managed runtime state the harness must stay
  agnostic to, not a stable test fixture (a standing project convention,
  not new to this change). The task explicitly instructs the agent not to
  touch the pre-planted buggy `app.py`, so the test's decisive assertion
  (`retries_used >= 1`) reliably comes from the harness's own automated
  verification catching it, not from the agent noticing it unprompted.
  Verified live: the agent left the fixture untouched, the harness's
  post-hoc verification caught the entrypoint-ordering failure (pytest
  alone had already passed), sent the automated follow-up, and the agent
  fixed it — final state `verified` after exactly 1 retry.
- **Third-party skills: own lockfile + SDK fetch, not the SDK's
  `InstallationManager`.** The SDK manager marks a new install
  `enabled=True`, and its `discover_untracked()` auto-enables any directory
  dropped into the install root. Both contradict the explicit-opt-in rule.
  It also records no license or integrity. Its
  `fetch_skill_with_resolution` (subpath containment, SHA resolution, full
  clone for a pinned SHA) and `Skill.load` are reused as-is. Enablement is
  enforced twice: at `enable` (CLI) and again at load (the lockfile is
  hand-editable). `update` disables on any content/license change. `sync`
  refuses a hash mismatch. Commands live under `certo-admin skills`,
  the existing argparse subcommand CLI, rather than a new entry point. The
  lockfile is JSON beside the gitignored dir, not in it, so it can be
  committed for reproducibility. Existing hand-placed
  `skills/frontend-design/` etc. are deliberately left loading as before
  (no silent behavior change); `install` refuses those names instead.
- **Run summary uses per-`usage_id` metrics, not the SDK's combined
  metrics** — the combined entry's model is `"default"`; each per-usage
  entry carries the real model name. Always computed (not gated on
  `CERTO_ARTIFACTS_DIR`), and read defensively in the `finally` so a
  metrics failure can't mask the run's own outcome or exception.
- **sdist is an explicit allowlist (`src/certo`, `tests`, the Dockerfile,
  README/MANUAL/LICENSE, `.env.example`, `bench.yaml.example`; the model
  examples ship inside `src/certo/examples/` since 0.1.10) plus
  explicit secret/state/cache excludes on both targets** — hatchling's
  default sdist relied on `.gitignore` alone to keep `.env`/`models.yaml`/
  `projects/` out, and shipped dev-only files (`.claude/`, `CLAUDE.md`,
  `todo.md`, `docs/`, `uv.lock`). Verified by building a copy with no
  `.gitignore` and planted decoys: none shipped. `tests/test_packaging.py`
  enforces the allowlist and the forbidden patterns.
- **First-party skills moved into the package (`src/certo/builtin_skills/`)
  and always load; `CERTO_SKILLS_DIR` (still `./skills`) became an
  additive user catalog that overrides built-ins by name.** A clean-venv
  wheel install proved the old cwd-relative `./skills` default loaded zero
  skills outside a repo checkout (nothing outside `src/certo` is in the
  wheel). Named `builtin_skills`, not `skills`, so it doesn't sit beside
  `skills.py`. Additive rather than "one dir replaces the other" so the
  README's drop-a-file workflow and hand-placed `skills/frontend-design/`
  copies keep working unchanged. `tests/test_packaging.py` builds the real
  sdist→wheel and checks the catalog ships.
- **`harness`/`harness-server`/`harness-admin` console aliases removed
  before the first PyPI release** (supersedes "they cost nothing" in the
  rename entry). There are no external users, and a globally installed
  `harness` could shadow another tool on a user's PATH. The `HARNESS_*`
  env-var fallback and legacy storage reads are unaffected — those protect
  local data, not command names. `tests/test_cli.py` asserts the declared
  and installed scripts are exactly the three `certo*` commands.
- **Release workflow: `verify` → `build` → `publish` jobs, trusted
  publishing only.** A PyPI version can never be reused, so the tag must
  equal `pyproject.toml`'s version and the suite must pass before anything
  is built; only the `publish` job (environment `pypi`) gets `id-token:
  write`, and it uploads exactly the artifact the `build` job checked with
  `twine check`. No ruff gate yet: `main` currently has lint/format
  findings. Tests asserting a tool is *absent* (`mvn`, `mypy`) now skip
  when it's installed, since GitHub's Ubuntu runner ships Maven.
- **`sqlalchemy` is in the `dev` extra, not `importorskip`-guarded** — the
  sqlite `SQLTaskStore` tests are the only automated coverage of the code
  path shared with mysql/postgres, so a plain `.[dev]` install must run
  them rather than silently skip them.
- **An unset reasoning effort means none for Ollama models; `none`/`off`
  pass an explicit `None`.** The SDK default `"high"` reaches Ollama as
  `think: true`, and Ollama rejects it for any model without a thinking
  mode (`qwen3-coder:30b`, the README quickstart model), failing the first
  call. Passing the string `"none"` through still sends `think: false`, so
  it becomes `None`, which the SDK's chat options skip entirely. That
  gives up OpenAI's literal `reasoning_effort="none"`: that request now
  gets the API's own default instead (accepted, per the user's request).
  Matched on the `ollama`/`ollama_chat` model prefix: only the default
  changes, never the provider. `tests/test_llm.py` asserts the wire request
  against a local fake Ollama that returns the real 400. The bug reproduces
  there with the old `build_llm`.
- **A Python project gets its own environment, shared by the agent's
  terminal and verification; Certo's own environment is never used.**
  Verification used `sys.executable`, which only had pytest in the dev
  venv (see "confident but wrong" #9). An existing environment is always
  reused before one is created: `uv.lock` through `uv run`, then
  `.venv`/`venv`. Only Certo-made venvs (marker file) are ever rebuilt; a
  broken user venv makes pytest `unavailable`, never deleted. pytest is
  auto-installed into the project environment only when test files exist,
  and a failed install is `unavailable`, not `failed`: a missing runner is
  a limitation, not a test failure. ruff/mypy are not auto-installed. They
  count only when installed in the project environment, since one on PATH
  says nothing about the project's own config. An empty workspace gets an
  environment up front only if the task names Python: creating one for
  every empty workspace would litter Node/Go projects.
- **Under `--execution docker`, verification runs inside the container
  (user's choice), not on the host.** A venv is tied to the OS that made
  it (interpreter symlinks, binary format), and the agent installs
  dependencies into the container's. Host-side verification could never
  see them: it already used Certo's own host interpreter before this
  change, so Docker verification of any project with dependencies was
  broken. Rejected: a separate host venv (same blindness) and local-only
  (leaves Docker broken). Detection/planning still read files on the host
  via the bind mount; commands go through `WorkspaceRunner` →
  `execute_command`. **Not run against a real container yet**: the Docker
  daemon wasn't usable in the session that built it. Covered by fake-
  workspace unit tests only.
- **`certo verify` is dispatched on `argv[0] == "verify"` exactly, before
  argparse** (user-approved). Subparsers would make a task positional and
  a subcommand compete, and argparse would reject or misroute existing
  task invocations. A task is one argument, so "verify the login flow"
  can't match. The only input whose meaning changed is the one-word task
  `verify`, still reachable as `certo -- verify`. It lives in `certo`, not
  `certo-admin`, because it's the user-facing check, not store
  maintenance.
- **Release check installs the wheel like a user (`scripts/release_check.sh`)
  and gates publishing on it**, because the pytest suite runs inside the dev
  venv and structurally can't see "works only in the dev venv" bugs. Bash,
  not Python: it must not run inside any Certo-related interpreter. It runs
  in the release workflow's `build` job against the exact `dist/*.whl`
  that `publish` uploads. There is no pull-request CI workflow to attach it
  to yet. The dependency fixture asserts its package is *not* importable
  from Certo's tool env, so a pass can't come from Certo's own packages.
  Since 0.1.4 it also runs `certo init --yes --no-check` (provider keys
  unset) and checks the files, the overwrite refusal, `certo check`'s
  missing-key message and the no-terminal `.env`: `init` reads package
  data, which only an installed wheel proves is shipped. Since 0.1.5 the
  whole script runs with a throwaway `XDG_CONFIG_HOME`; `init --yes` must
  write the user file and `certo check` from another folder must name it
  as the source, and `init --yes --local` covers `FOLDER/.env`.
- **Versioning: every feature bumps the third digit, in the same commit**
  (user's rule; full text in CLAUDE.md). The first two digits move only on
  the user's decision. The version is written literally in
  `pyproject.toml` and `certo/__init__.py`, not read from installed
  metadata, because the Docker image imports `certo` from source with no
  dist-info. `tests/test_version.py` keeps those two and `uv.lock` equal.
  `--version` is on all three commands. `certo-server` parses its
  arguments before importing uvicorn, so `--version` works without the
  `server` extra. `--version` was the first feature under this rule
  (0.1.1 → 0.1.2), and the `CERTO_LLM_` rename made it 0.1.3. 0.1.2 was
  never published on its own.
- **LLM settings renamed `LLM_*` → `CERTO_LLM_*`, with no fallback** (user's
  choice, 0.1.3). The bare names are generic, and other tools set them too.
  Unlike the `HARNESS_*` rename, the old names are never read, because a
  fallback would still let another app's `LLM_MODEL` leak in. They are only
  named, never echoed, in the "required" `ConfigError`s
  (`config._old_llm_names_hint`), so a 0.1.0/0.1.1 setup gets told what to
  rename. The SDK itself never reads `LLM_*` (checked: no reference in
  `openhands/`), so `config.py` is the only reader.
- **`certo init` is interactive, with no `--api-key` flag, and keeps model
  defaults in one data file** (0.1.4). Most first-run failures were model
  setup (wrong address, missing key, a rejected setting), so init asks only
  what `.env` needs and ends with a real tool call, which is what the agent
  needs; a plain text reply would pass a model that then stalls the agent.
  The check goes through `make_llm_completion`, the agent's own call, so
  Responses vs Chat Completions and prompt-based tool calling match a run.
  A key comes from `getpass` or the provider's own exported variable, never
  argv (shell history), and an exported key is written as `${VAR}` rather
  than copied. Without a TTY nothing is asked, so scripts and CI never hang.
  Defaults live only in `starter/providers.toml`, each with its `source`
  and `checked` date. They were picked from each provider's model page and
  confirmed in LiteLLM's model map; re-check both before each release. All
  three cloud defaults need LiteLLM >= 1.105 for pricing, which a fresh
  install gets. The dev lock (1.100.1) runs them with an unknown cost.
  `init` and `check` dispatch on `argv[0]` exactly, like `verify`.
- **`LITELLM_MODE` defaults to `PRODUCTION`** (0.1.4). LiteLLM's import
  calls `load_dotenv()` with no path when it is `DEV`, and python-dotenv
  then searches upward from LiteLLM's own install folder: a venv inside the
  checkout loaded the repo's `.env` from any directory, and a tool install
  can load `~/.env`. Those values beat `./.env`, which config.py loads
  without overriding. Found when `certo check` passed in an empty folder.
  The variable gates nothing else in LiteLLM (checked).
- **`check-llm` lives in `certo-admin`, not the `certo` CLI** — `certo`
  requires a task positional, while `certo-admin` is already the
  subcommand-based maintenance CLI. There's no `--api-key` flag, so a key
  never lands in shell history; use `CERTO_LLM_API_KEY=... certo-admin check-llm`.
  Retries are disabled so a bad key/endpoint fails in seconds, not after
  the SDK's 5 backoff retries.
- **A user-level settings file, `$XDG_CONFIG_HOME/certo/.env`** (0.1.5).
  Without it, working one project at a time meant copying a `.env` with
  the key into every project, which is how keys end up committed, or
  exporting variables in every terminal. XDG with a `~/.config` fallback
  on every platform, not each OS's own config folder, so there is one
  path to document and to type. `certo init` saves there by default and
  `--yes` picks it; without a terminal it still writes `FOLDER/.env`, as
  before.
- **Precedence: environment, then `./.env`, then the user file, each
  variable on its own** (0.1.5). Specific beats general, so one project
  can change only `CERTO_LLM_MODEL` and keep the shared key. Implemented
  as fill-only (a source never replaces a value an earlier one set),
  which is also `load_dotenv(override=False)`'s rule, so nothing can
  silently win over a higher source. A blank value counts as unset, as in
  `_read`: `init` writes `CERTO_LLM_API_KEY=` as a placeholder, and that
  mustn't hide the user file's key. Tests set `XDG_CONFIG_HOME` in
  `conftest.py` at import time (some modules call `load_config()` at
  collection) and restore `os.environ` after each test, since loading
  writes to it.
- **The "existing folder" warning never blocks or asks** (0.1.5). It runs
  before every CLI task, including scripts and CI where nobody can
  answer, and a question there would hang or fail a run that was fine.
  The decision to commit first is the user's; Certo only says when there's
  no way back. Only changes under the task's folder count. Certo-created
  `--project` folders are listed beside the projects, in
  `CERTO_PROJECTS_DIR/.certo-created-projects`, rather than marked inside
  them, so a generated project carries no Certo file. Silenced with
  `CERTO_NO_WORKTREE_WARNING`, a setting rather than a flag, so the user
  file can turn it off everywhere.
- **User docs moved from one `MANUAL.md` to a `docs/` folder in the repo,
  not a GitHub wiki.** The manual had grown to ~2,300 lines mixing three
  readers: newcomers, people looking up a flag, and maintainers. A wiki is
  versioned apart from the code, can't be changed in the same commit as
  the behaviour it describes, and can't be tested; `docs/` can. Structure:
  one getting-started path, task guides, exact reference pages, and
  concept pages, kept separate so each page has one reader (a
  "Diátaxis"-style split), plus troubleshooting written as symptom →
  cause → fix. Plain GitHub Markdown, no site generator yet. Staleness:
  `tests/test_docs.py` derives the lists from the code (settings recorded
  while `load_config()` runs, argparse parsers walked for every flag and
  subcommand, `VERIFICATION_STATES` and `_FAILING_STATES` for the verdict
  table) and fails on a missing entry or a broken relative link or
  heading anchor; prose correctness is still a review duty (CLAUDE.md).
  Maintainer-only notes ("verified live", SDK line references) stay here,
  not in `docs/`. `MANUAL.md` became a redirect table so old links and
  code comments that name a manual section still lead somewhere.
- **The model-call timeout is a setting: `CERTO_LLM_TIMEOUT_SECONDS`
  and per-entry `timeout_seconds` in `models.yaml`, both default 300**
  (0.1.8, user request: local models went past 300 s). It is the SDK's own
  `LLM.timeout` (default 300, `None` = no limit, which `0` maps to). It
  matters more than it looks: the SDK retries `litellm.Timeout` (in
  `LLM_RETRY_EXCEPTIONS`, `num_retries=5`) and each retry restarts the
  generation, so a model needing 400 s per answer never gets one and spends
  ~30 min, the whole default task budget. A catalog entry doesn't inherit
  the `.env` value (entries are complete specs, like `api_key`). The
  verification checks' own 300-second limit is unrelated and unchanged.
  `certo check`/`check-llm` keep their short timeout.
- **Command-line resume state lives in the project's `.certo/`, built on
  the SDK's own conversation persistence** (0.1.7, user's choice of
  location). The task store was server-only, so an interrupted CLI run
  lost the agent's context whatever backend was configured. Reusing
  `Conversation(persistence_dir=, conversation_id=)` (golden rule 1)
  gives exact context back; verified in-session that a second
  `Conversation` with the same id reloads the events, accepts a different
  model, and writes no API key (secrets are redacted without a cipher).
  `STATUS.md` is written by Certo, not the agent, so it is trustworthy and
  doubles as the fallback memory when the conversation can't be reopened.
  Supersedes, for this one folder, the 0.1.5 "a generated project carries
  no Certo file" rule: `.certo/` holds a `.gitignore` of `*`, so git (and
  the worktree warning, which also skips it when checking for an empty
  folder) ignores it without editing the user's `.gitignore`. Only the
  last run is kept (each conversation can be megabytes; artifacts keep
  history). The server keeps its `TaskStore`: concurrent tasks, queries
  and TTLs need a real store, not Markdown files. Not done: a resume
  after a kill mid-tool-call relies on the SDK handling the unmatched
  action; not exercised against a live model.
- **Escalation (0.1.9): start cheap, climb only when verification fails.**
  Per task, not per step: the signal is Certo's own verdict, which only
  exists at the end of a run. Opt-in (`--escalate`,
  `CERTO_MODEL_SELECTION=escalate`, server `escalate`); single-model runs
  and `--auto-model` ranking are untouched (working agreement 2).
  `--escalate` with `--auto-model`, `--model` or `--resume` is an error:
  the ladder decides the models, and resume continues one conversation.
- **`activated: false` means never used, everywhere** (0.1.9, supersedes
  the bench entry below that ignored it): not in `--auto-model` (already
  so), escalation or `certo bench`. A bench arm naming an inactive model
  is an error with how to reactivate; a ladder rung on one is skipped with
  a warning; a ladder left empty is an error.
- **Ladders are explicit or derived.** Explicit (`escalation.ladders`)
  always wins; `--escalate` with no name uses `default`, else derives.
  Derived: capability = the plain sum of a model's ratings except the cost
  axis (`cost`, configurable), i.e. reasoning + precision + code with the
  usual axes; capped at `max_rungs` (default 3, minimum 2) by
  floor(j(n-1)/(k-1)+0.5), which keeps the first and last kept model
  and spreads the rest. Deterministic, printed, written to
  MODEL_DECISIONS.md.
- **Derived ladders start from the best of the cheapest, not the weakest**
  (0.1.11, user's call; supersedes "ascending capability, ties to the
  higher cost rating" from 0.1.9). Weakest-first put a model on the first
  rung that another one beat at the same price (a real catalog: devstral 5
  ahead of qwen3.8 8, both free, and the 3-rung spread then cut qwen3.8
  entirely). Now: cheapest cost rating first, most capable within it, then
  keep a model only if it beats every model kept before it (the Pareto
  front of cost against capability); the beaten ones go in
  `ResolvedLadder.skipped` with the model that beats them, shown by
  `certo check` and before a run. No cost rating = most expensive; no cost
  rating anywhere = the old capability order (no price to compare, else
  only one rung would be left). Speed was considered for the first rung
  but the catalog has no speed data, and a `speed` rating would count as
  capability. Changes the derived ladder of a bench `escalate` arm with no
  `models:`. **Not benchmarked** on a local and a cloud model yet
  (working agreement 2): no session with both has run it.
- **Bench plan prices a derived escalate arm on its real ladder, and adds
  a "likely" cost** (0.1.12, user's question). The plan priced every
  active model for a derived arm (`Arm.models` holds them all), while a run
  uses only `derive_ladder()`'s ≤ `max_rungs` rungs: $58.95 shown against
  $24.30 worst case on a real file. The plan now derives the ladder;
  `Arm.models` is unchanged because it feeds the `--resume` fingerprint.
  "At most" stays (every rung runs), since it is the safe bound. "Likely"
  = Σ rung cost × P(reaching it), the climb rates taken from earlier
  results under the same parent folder: single-arm runs and escalation
  rungs, an escalating verdict or an error/provider failure counting as a
  climb, matched by name *and* model id. Shown only when every rung but
  the last has history, rather than guessing. Token counts per run are
  still the fixed 500k/20k guess (see the backlog item on recorded cost).
- **Bench records its real cost per model, beside the estimate** (0.1.13,
  user request). Per-run and per-arm cost already existed; missing were a
  total, a per-model split and a comparison. `bench_report.cost_summary`
  builds them from the run records alone (escalation split by rung via
  each rung's own `cost`), written to `results.md` (## Cost), a new
  `cost.json`, and printed at the end. The plan's estimate is stored in
  `meta.json` (`estimate`) when the folder is created, outside
  `config`, so the `--resume` fingerprint is unaffected; older folders
  simply have none.
- **Bench keeps each run's conversation** (0.1.15, user request): the
  fooled run behind `unchanged` couldn't be explained, since bench passed
  no `on_message` and set no `CERTO_ARTIFACTS_DIR`. `execute_run` wraps the
  stream to collect messages (strategies unchanged) and writes
  `runs/transcripts/<run_id>.json` before grading, also when the strategy
  raises. A subfolder, not `runs/<id>.transcript.json`, because
  `load_records` globs `runs/*.json`. Not artifacts (`write_run_artifacts`):
  that adds per-rung folders and metadata the run record already holds.
- **A `verified` run that changed no file becomes `unchanged`, after one
  follow-up** (0.1.14, user's choice among: always `inconclusive`, always
  a failure, follow-up only). The checks then only prove the starting
  folder passed, which was true before the agent ran ("confident but
  wrong" #10). Certo can't tell "nothing to do" from a lazy or misdirected
  model, so it asks once (cheap, catches stopping early and edits written
  outside the folder, and the message names the folder), then refuses to
  take the agent's reason as proof (golden rule 7). Not `inconclusive`:
  that never climbs, and "nothing to check" differs from "did nothing".
  Not a failure: "check the tests pass" is a legitimate no-change task, so
  it exits 0 like `inconclusive` (`runner.UNPROVEN_STATES`, which
  `--require-verification` / `require_verification` fail). Escalation
  climbs on it, but two consecutive `unchanged` rungs stop the climb: two
  models agreeing is evidence, and climbing on would send a genuine
  no-change task to the most expensive model. Only after `verified` (every
  other verdict already isn't success); never on `--resume` (changes may
  predate the session). A change is the escalation before/after listing
  (`workspace_listing`, which now also skips `target`/`.gradle`, written
  by verification itself) minus `MODEL_DECISIONS.md`. The follow-up counts
  as one fix attempt in `retries_used`. A Rust project with no
  `Cargo.lock` gets one from `cargo test`, which counts as a change: a
  miss toward the old behaviour, accepted.
- **A local model's cost is zero, not unknown** (2026-10-18, found by the
  first complete benchmark: every total said "+ unknown" because the local
  arm's 27 runs had tokens and no price). `run_summary.ModelUsage.cost_known`
  is true for an id with a local prefix (`model_pricing.is_local_model_id`,
  the prefixes `is_local` already used); the metrics carry only the model
  id, so an `openai/` model on a local `base_url` is still "unknown".
  `bench_report` applies the same rule to older records, so a regenerated
  report is right. Same day: `meta.json` gained `ladders` (a derived
  escalate arm's real ladder, outside `config` so the `--resume`
  fingerprint is unchanged), shown in the Models column instead of every
  active model.
- **The model catalog is split from personal settings (0.1.10, user's
  design):** `models_list.yaml` (model ids, descriptions, ratings,
  `reasoning_effort`, `timeout_seconds`, task profiles, escalation
  ladders) and `models.yaml` (by name: `api_key`, `base_url`,
  `activated`, overrides of ratings per axis, `reasoning_effort`,
  `timeout_seconds`, `description`). So the catalog can be shared and
  updated without touching keys. Both ship only as `.example` files in
  the package and are never read from there: a release must never
  overwrite a user's customised list, and using the example silently
  would hide that the user has no keys configured. `models.yaml` may only
  name models the list has; new models go into the list. Personal fields
  in the list and the old single-file `models.yaml` are errors that say
  what to move (no compatibility reader: the user migrates by hand).
  Lookup mirrors `.env` (project folder before user folder) but takes the
  first file found whole rather than merging entries, so what runs is one
  file you can open. Tests never look in the repository root
  (`conftest.py`), where a developer's real `models.yaml` lives.
- **Capability ignores task profiles** (changed before release, user's
  call, with `models.yaml.example`'s rating comments as the source of
  truth). The brief first had the matched profile's weighted sum; the
  ratings are now anchored to cross-provider benchmarks, and a ladder
  climbs by general capability, so the same ladder serves every task and
  the ladder printed by `certo check` is the one a run uses. The sum is
  over every axis but the cost axis (not hard-coded to the three names),
  so a catalog with other axis names still orders; a cost rating under
  another name must be named by `escalation.cost_axis`.
- **What climbs:** `retry_exhausted`, `no_progress`, `timed_out`,
  `incomplete`, `stuck`, `unchanged` (0.1.14, see below);
  `acceptance_failed` only when the ladder opts in.
  Never `inconclusive` (no signal: a stronger model faces the same blank),
  `budget_exhausted` or `confirmation_required` (the user's limits). A
  provider failure climbs too, recorded as such; on the last rung it is
  raised like in a single-model run.
- **A fresh conversation per rung, same workspace, handoff from facts.**
  Replaying the previous conversation would cost money and add noise (a
  real local run sent 344k input tokens for hello-world). The next rung
  gets the files, the task, the bounded failing-check output Certo sends
  on a retry, and a note Certo writes from recorded facts (model, verdict,
  fix attempts, files from a before/after listing, failing checks). The
  listing is used rather than `git status`, because it is exact to the
  rung even when the folder already had uncommitted changes. Continue-only
  for now (restart is in the backlog).
- **Budgets:** `CERTO_MAX_TASK_SECONDS` spans every rung; each rung has its
  own `retries` (default `CERTO_MAX_VERIFY_RETRIES`). New
  `CERTO_MAX_TASK_COST` (USD, unset) is checked before each rung against
  the recorded per-model cost; unknown prices count as 0 and are named. It
  applies to escalation only.
- **Escalation under Docker is supported.** Each rung is a new
  `Conversation` on the same `DockerWorkspace` (public API: the SDK opens
  a new conversation on the same agent-server, same container and bind
  mount). The remote conversation wraps every failure in a server error,
  so under Docker any `ConversationRunError` ends the rung ("provider or
  run failure"); locally only the SDK's `LLMError` does, and any other
  error is raised at once.
- **One consistency check for `models.yaml`** (`catalog_check.py`), shared
  by every command that reads it, so `certo check` reports exactly what a
  run would refuse. Two readings of the brief: a "duplicate rung" is the
  same model with the same settings (the same model at another
  `reasoning_effort` is a legitimate rung); an unknown `cost_axis` is an
  error only when written explicitly, since the default `cost` must not
  break catalogs without cost ratings.
- **`certo check --models` builds each model's config from its entry
  alone** (nothing from `.env`), as runs do, and rewrites
  `llm_check.explain()`'s `.env` field names into the `models.yaml` ones.
- **Server rungs in the SQL store: a nullable `rungs` column added on
  startup** with `ALTER TABLE ... ADD COLUMN` when missing (user's choice
  over hiding it in `completion_contract` or leaving SQL stores without
  it). Old rows read as `None`.
- **Bench `strategy: escalate`:** `models: [...]` (at least two, active, no
  repeats) or derived; `escalation.ladders` in `models.yaml` are
  not used (in `models_list.yaml` since 0.1.10), so an arm states its
  ladder in `bench.yaml`. "Cost per solved
  task" is added for every arm (also meaningful for `single`); rung
  shares only for escalate arms; existing columns unchanged.
- **`certo bench` grades with hidden tests, takes models from
  `models.yaml` by name (since 0.1.10 the ratings are in `models_list.yaml`), and puts strategies in a registry** (0.1.6).
  Hidden tests, because the agent's own tests share its misunderstandings
  (the Hanoi and Wordle cases): only tests it never saw can show whether
  Certo was fooled, which is the number Certo exists to keep at zero.
  `models.yaml` names, not `.env`: `.env` holds one model by design,
  while a benchmark compares several; the catalog already holds keys,
  gitignored, so `bench.yaml` stays key-free and committable, and each arm
  says exactly which model runs (no `--auto-model` ranking; `activated`
  was ignored until 0.1.9, superseded above). A registry, because the next strategies (`cascade`,
  `best_of`) must be measurable the moment they exist: each is one class
  that parses its own arm keys and runs one task, and the runner, grader
  and report never change. "Caught" follows the spec literally (agent
  finished, not `verified`); `unconfirmed_pass` is recorded beside it
  because a correct project with no tests also lands there. Runs are
  repeat-major so a stopped benchmark has some of every arm and task.
