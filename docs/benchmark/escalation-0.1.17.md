# Benchmark: escalation in Certo 0.1.17

One `certo bench` run on the 9 bundled tasks, with two ladders: a local
model first, then `claude-haiku-5-5` when the local model fails. It
answers one question: since 0.1.16, does Certo move on to the next model
when the first one did no work? The single-model results it compares
with are in [Baseline 0.1.15](baseline-0.1.15.md).

## The setup

- **Certo:** 0.1.17. **Task set:** version 1 (`11b1105b535e`, bundled),
  9 tasks: 6 Python, 3 Node.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 8 CPUs,
  16 GB RAM. The local models ran on Ollama on another machine, the same
  setup as the 0.1.15 baseline.
- **Run:** 2026-10-18, from 20:58 UTC. 1 repeat, so 9 runs per arm.
- **Results folder:** `bench-results/20261018-215755`, on the machine
  that ran it.

| Arm | Rung 1 | Rung 2 |
|---|---|---|
| `q36-ladder` | `ollama/qwen3.6:35b-a3b` | `anthropic/claude-haiku-5-5` |
| `q38-ladder` | `ollama/qwen3.8:27b` | `anthropic/claude-haiku-5-5` |

The two local models were picked from the 0.1.15 baseline. Alone,
`qwen3.6` passed 0 of 27 runs, almost always because it wrote its tool
calls as text and the run ended with an empty folder. `qwen3.8` passed
24 of 27, and failed the same way 3 times.

## Results

| Arm | Hidden tests passed | Verified | Fooled | Unconfirmed passes | Median time | Cost | Cost per solved task |
|---|---|---|---|---|---|---|---|
| `q36-ladder` | 9/9 | 8/9 | 0 | 1 | 1m 03s | $0.094 | $0.0105 |
| `q38-ladder` | 9/9 | 9/9 | 0 | 0 | 7m 44s | $0.019 | $0.0021 |

Total cost: **$0.11**, all of it haiku.

Which rung produced the final result:

| Arm | Rung 1 (local) | Rung 2 (haiku) |
|---|---|---|
| `q36-ladder` | 1 of 9 | 8 of 9 |
| `q38-ladder` | 7 of 9 | 2 of 9 |

## What the results say

- **Escalation climbed.** It is the first Certo benchmark where it did:
  10 of 18 runs moved to haiku, and haiku passed the hidden tests in all
  10. Every climb was a local model that did no work: 5 ended
  `inconclusive` with an empty folder, 5 ended `unchanged`. Before 0.1.16,
  the 5 `inconclusive` runs would have stopped on rung 1, with nothing
  done.
- **A failed local rung costs little time, most of the time.** The
  `qwen3.6` rungs that did no work took a median of about 18 seconds
  before haiku took over. The slowest took 4.5 minutes, and one `qwen3.8`
  rung took 10 minutes before it wrote a tool call as text.
- **With `qwen3.8` first, the ladder cost about a quarter of haiku
  alone.** qwen3.8 solved 7 tasks for free and haiku the other 2, for
  $0.019. In the 0.1.15 baseline, haiku alone cost $0.085 for the same 9
  tasks. The price is time: a median of 7m 44s per task, against 45s for
  haiku alone.
- **With `qwen3.6` first, the ladder is haiku with a short delay.** It
  cost about the same as haiku alone ($0.094 against $0.085). On this
  Ollama setup, the local rung adds nothing.
- **Certo wasn't fooled.** No run was `verified` with failing hidden
  tests.

## The one run that stayed on a failed rung

`q36-ladder` · `temperature-table`. `qwen3.6` wrote `temperature.py`,
then wrote its test file as a tool call in text, and the run ended there.
The folder had code but no tests, so there was nothing for Certo to run:
the rung ended `inconclusive`. Since it had written a file, it didn't
count as "did no work", so the ladder stopped, as designed. The code
happened to be correct (the hidden tests passed), so this is the one
"unconfirmed pass". A run that ended this way with wrong code would also
have stopped there, without asking haiku.

## Reproduce this run

The benchmark file is
[bench-0.1.17-escalation.yaml](bench-0.1.17-escalation.yaml). Copy it,
enable its models in your `models.yaml`, and run:

```bash
certo bench --config bench-0.1.17-escalation.yaml
```

Your numbers will differ: models vary between runs, and local times
depend on the machine serving the model.

## Limits of this run

- One repeat: 9 runs per arm, so a difference of a run or two can be
  chance.
- The single-model numbers it is compared with come from a different
  run (0.1.15), not from arms in this one.
- Nine small tasks, which haiku solves alone. The run shows that the
  ladder climbs and what it costs; it can't show a ladder solving tasks
  that no single model solves.
- Every climb here was a model that did no work. A climb after a
  `failed` verification, and the handoff of half-done work, are still
  unmeasured.

## Related

- [Baseline 0.1.15](baseline-0.1.15.md): each model alone
- [Escalate between models](../guides/escalate-between-models.md)
- [Choose a local model](../guides/choose-a-local-model.md)
- [Benchmark models and strategies](../guides/benchmark.md)
