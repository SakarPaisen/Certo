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

## Moved

- Every backlog item (optional, growth, skills): `TODO.md`.
- Module notes and internal limitations: `ARCHITECTURE.md`.
- The decisions log: `DECISIONS.md`.
