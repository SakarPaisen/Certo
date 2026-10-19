# Benchmark baseline: Certo 0.1.18, local models

One `certo bench` run on the 9 bundled tasks, with two local models, three
times each. It answers one question: which local model should Certo
suggest first? Until now the default was `qwen3-coder:30b`, which had
never been measured. How the benchmark works, and what each column means,
is in [Benchmark models and strategies](../guides/benchmark.md). The
previous baseline is [0.1.15](baseline-0.1.15.md).

## The setup

- **Certo:** 0.1.18. **Task set:** version 1 (`11b1105b535e`, bundled),
  9 tasks: 6 Python, 3 Node.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 8 CPUs,
  16 GB RAM.
- **Models:** on Ollama 0.40.6, on another machine, both with a context
  length of 131,072 tokens and Q4_K_M quantization (read from Ollama's
  `/api/version` and `/api/ps` during the run). Each model call could
  take up to 1200 seconds (`timeout_seconds`) for both models.
- **Run:** 2026-10-19, 08:05 to 15:25 UTC. 3 repeats, so 27 runs per
  model.
- **Results folder:** `bench-results/0.1.18-local`, on the machine that
  ran it.

| Arm | Model |
|---|---|
| `qwen3-coder` | `ollama/qwen3-coder:30b` |
| `qwen3.8` | `ollama/qwen3.8:27b` |

## Results

| Arm | Hidden tests passed | Verified | Fooled | Caught | Unconfirmed passes | Median time | Tokens in |
|---|---|---|---|---|---|---|---|
| `qwen3.8` | **27/27** | 26/27 | 0 | 1 | 1 | 7m 37s | 4.3 million |
| `qwen3-coder` | 18/27 | 14/27 | **3** | 12 | 7 | 8m 20s | 24.2 million |

Both cost $0.00. No run stopped with an error.

Hidden tests passed, per task (out of 3):

| Task | `qwen3.8` | `qwen3-coder` |
|---|---|---|
| duration-parser | 3 | 2 |
| inventory-fix | 3 | 3 |
| page-ranges | 3 | 3 |
| pedestrian-crossing | 3 | 1 |
| semver-order | 3 | **0** |
| slugify | 3 | 2 |
| temperature-table | 3 | 3 |
| token-bucket | 3 | 1 |
| wordle-score | 3 | 3 |

## What the results say

- **`qwen3.8:27b` is the better local default.** It passed every hidden
  test, was never wrong when Certo said `verified`, was a little faster,
  and used less than a fifth of the input tokens. So Certo now suggests
  `ollama/qwen3.8:27b`, not `qwen3-coder:30b`.
- **`qwen3-coder:30b` wrote wrong code more often.** Its 9 failed runs
  were coding mistakes, not setup problems: it never wrote a tool call as
  text. It failed `semver-order` all three times.
- **Certo was fooled 3 times, all by `qwen3-coder`** (see below). Of the
  9 runs whose hidden tests failed, Certo said `verified` for 3 and
  stopped the other 6 (`retry_exhausted` or `no_progress`).
- **8 runs had correct code but a failing verdict** (the "unconfirmed
  passes", 7 of them `qwen3-coder`). In 7, the agent's own tests still
  failed after two fix attempts, although the code passed the hidden
  tests; the eighth ran out of time. Certo can't tell a wrong test from
  wrong code, so it reported the failing check.
- **Tool calls written as text were rare.** `qwen3.8` wrote a tool call
  as plain text in 3 runs; 2 of them recovered and ended `verified`. In
  the 0.1.15 baseline this ended all 3 of its failed runs. The context
  length this time was 131,072; in 0.1.15 it wasn't recorded, so the
  setup change can't be proven to be the reason.

## Compared with 0.1.15

| Arm | 0.1.15 | 0.1.18 |
|---|---|---|
| `qwen3.8` | 24/27, 0 fooled, 4m 37s | 27/27, 0 fooled, 7m 37s |

The Ollama setup changed between the two runs (0.1.15's context length
wasn't recorded), so the times can't be compared. The three runs that
failed in 0.1.15 all ended on a tool call written as text; here only one
run ended on one, and its code was correct.

## The fooled runs

All three are the gap described in
[Write a task Certo can check](../guides/write-a-good-task.md#3-give-the-expected-answers-yourself):
the code passed every test the agent wrote, and the agent's tests missed
a rule the task states.

- **`semver-order` · repeats 1 and 3.** The same two bugs both times.
  The task says prereleases are compared identifier by identifier; the
  code compared them as whole strings, so `2.1.0-dev.beta` came after
  `2.1.0-dev-x` (`.` sorts after `-`), not before. The task also says no
  identifier may be empty; the code accepted `1.2.3-` and `1.2.3+`.
- **`duration-parser` · repeat 3.** The task says every number is
  followed by a unit; the code accepted `"1h30"`, a number with no unit,
  instead of raising `ValueError`.

## Reproduce this run

The benchmark file is [bench-0.1.18-local.yaml](bench-0.1.18-local.yaml).
Copy it, enable both models in your `models.yaml`, and run:

```bash
certo bench --config bench-0.1.18-local.yaml
```

Expect about 7 hours with the models on a separate machine. Your numbers
will differ: models vary between runs, and local times depend on the
machine serving the model.

## Limits of this baseline

- Nine small tasks, and two models. It shows `qwen3.8:27b` is the better
  of the two, not that it is the best local model:
  `gemma4:31b-it-qat` passed 26 of 27 in 0.1.15, but took about three
  times as long.
- One Ollama setup. A smaller context length, or another quantization,
  may give different results.
- Certo 0.1.18. Since then, 0.1.19 tells the agent to keep the `.certo/`
  folder, a change these runs didn't have (the benchmark never creates
  that folder).
- `qwen2.5-coder:7b`, the suggestion for smaller machines, wasn't
  measured. Expect it to be weaker than both.

## Related

- [Baseline 0.1.15](baseline-0.1.15.md)
- [Escalation in 0.1.17](escalation-0.1.17.md)
- [Choose a local model](../guides/choose-a-local-model.md)
- [Benchmark models and strategies](../guides/benchmark.md)
- [Ollama and local models](../guides/ollama-and-local-models.md)
