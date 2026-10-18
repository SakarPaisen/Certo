# Benchmark baseline: Certo 0.1.13

The first complete `certo bench` run: one local model and one cloud model,
alone and in two escalation ladders, on the 9 bundled tasks. It is the
starting point that later versions are compared with. How the benchmark
works, and what each column means, is in
[Benchmark models and strategies](../guides/benchmark.md).

## The setup

- **Certo:** 0.1.13. **Task set:** version 1 (`11b1105b535e`, bundled),
  9 tasks: 6 Python, 3 Node.
- **Date:** 2026-10-17 22:15 to 2026-10-18 01:40 UTC.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 8 CPUs,
  16 GB RAM. The local model's speed depends on the machine serving it,
  which the results don't record.
- **Repeats:** 1. Every arm has 9 runs, so a difference of one or two runs
  between arms can be chance.

| Arm | Strategy | Models |
|---|---|---|
| `local` | single | qwen3.8-27b-local (`ollama/qwen3.8:27b`) |
| `cloud` | single | claude-sonnet-5-5 (`anthropic/claude-sonnet-5-5`) |
| `ladder` | escalate | qwen3.8-27b-local → claude-haiku-5-5 → claude-sonnet-5-5 → claude-opus-5-5 |
| `derived` | escalate | the ladder derived from the ratings: qwen3.8-27b-local → claude-haiku-5-5 → claude-opus-5-5 |

## Results

| Arm | Hidden tests passed | Verified | Fooled | Caught | Median time | Cost | Cost per solved task |
|---|---|---|---|---|---|---|---|
| `local` | 9/9 | 9/9 | 0 | 0 | 6m 13s | $0.00 | $0.00 |
| `cloud` | 9/9 | 9/9 | 0 | 0 | 37s | $1.12 | $0.12 |
| `ladder` | 8/9 | 9/9 | **1** | 0 | 6m 50s | $0.00 | $0.00 |
| `derived` | 9/9 | 9/9 | 0 | 0 | 8m 38s | $0.00 | $0.00 |

Total cost: **$1.12**, all of it the cloud arm. The plan had estimated at
most ~$70.20.

Time per run, in minutes (**FAIL** = the hidden tests failed):

| Task | `local` | `cloud` | `ladder` | `derived` |
|---|---|---|---|---|
| duration-parser | 9.7 | 0.4 | 6.2 | 11.6 |
| inventory-fix | 3.4 | 0.7 | 4.7 **FAIL** | 8.6 |
| page-ranges | 6.5 | 0.6 | 6.9 | 7.4 |
| pedestrian-crossing | 6.2 | 0.5 | 11.3 | 12.7 |
| semver-order | 10.9 | 0.8 | 6.8 | 9.6 |
| slugify | 5.7 | 0.5 | 9.4 | 11.7 |
| temperature-table | 2.8 | 0.4 | 6.3 | 7.7 |
| token-bucket | 4.2 | 0.7 | 7.1 | 4.5 |
| wordle-score | 8.8 | 0.7 | 4.4 | 4.2 |

## What the results say

- **The local model solved every task, like the cloud one.** Across the
  three arms that ran it, qwen3.8-27b-local passed the hidden tests in 26
  of 27 runs. It was about ten times slower than claude-sonnet-5-5 (6m 13s
  against 37s, median) and cost nothing.
- **No run needed a fix attempt.** Every run was `verified` on the first
  check, so Certo's retry loop was never used.
- **Escalation was not tested.** Both escalation arms finished every task
  on their first rung, the local model, so no task climbed to a cloud
  model. These tasks are too easy to tell the models apart; harder tasks
  are needed to measure escalation.
- **Certo was fooled once.** See below.
- **The cost estimate was far too high.** It prices every run at about
  500,000 input tokens; a claude-sonnet-5-5 run here used a median of
  about 124,000 (median cost per run: $0.12).

## The fooled run

`ladder` · `inventory-fix`: the task asks to fix and extend a small Python
module, `inventory.py`, whose existing tests already pass. The agent ran
for 4.7 minutes and used 117,430 input tokens, but **changed no file**:
the folder at the end was exactly the starter. The existing tests passed,
so Certo said `verified`, and the hidden tests failed
(`ImportError: cannot import name 'OutOfStock'`).

This was a real gap: passing checks prove nothing when nothing changed.
Certo 0.1.14 adds the [`unchanged`](../reference/verdicts.md#unchanged-in-more-detail)
verdict for this case: it asks the agent once more, and if no file
changes, the verdict is `unchanged`, not `verified`. The benchmark kept no
transcript then, so it isn't known whether the agent stopped early or
wrote its files somewhere else. Since 0.1.15 every benchmark run keeps
its conversation.

## Limits of this baseline

- One repeat, nine small tasks, one local and one cloud model.
- Escalation never climbed, so the ladders were not really compared.
- The results were reported with Certo 0.1.15's report, which counts a
  local model as free instead of "unknown"; the runs themselves are
  unchanged.

## Related

- [Benchmark models and strategies](../guides/benchmark.md)
- [Escalate between models](../guides/escalate-between-models.md)
- [Verdicts](../reference/verdicts.md)
