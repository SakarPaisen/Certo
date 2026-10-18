# Benchmark baseline: Certo 0.1.15

Two `certo bench` runs on the 9 bundled tasks: four local models, three
times each, and three cloud models, once each. Every model ran alone. It
answers which models to start with, and how often Certo was fooled, with
strong and weak models. How the benchmark works, and what each column
means, is in [Benchmark models and strategies](../guides/benchmark.md).
The previous baseline is [0.1.13](baseline-0.1.13.md).

## The setup

- **Certo:** 0.1.15. **Task set:** version 1 (`11b1105b535e`, bundled),
  9 tasks: 6 Python, 3 Node.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 8 CPUs,
  16 GB RAM.
- **Local run:** 2026-10-18, 08:14 to 19:55 UTC. 3 repeats, so 27 runs
  per model. The models ran on Ollama on another machine; its Ollama
  version and context length weren't recorded, so the local times are
  only comparable with each other.
- **Cloud run:** 2026-10-18, 20:11 to 20:34 UTC. 1 repeat, so 9 runs per
  model.
- **Results folders:** `bench-results/20261018-091449` (local) and
  `bench-results/20261018-211119` (cloud), on the machine that ran them.

| Arm | Model |
|---|---|
| `gemma4-qat` | `ollama/gemma4:31b-it-qat` |
| `qwen3.8` | `ollama/qwen3.8:27b` |
| `devstral` | `ollama/devstral-small-2:24b` |
| `qwen3.6` | `ollama/qwen3.6:35b-a3b` |
| `haiku` | `anthropic/claude-haiku-5-5` |
| `luna` | `openai/gpt-6-luna` |
| `sonnet` | `anthropic/claude-sonnet-5-5` |

## Results

| Arm | Hidden tests passed | Verified | Fooled | Caught | Unconfirmed passes | Median time | Cost per solved task |
|---|---|---|---|---|---|---|---|
| `sonnet` | 9/9 | 9/9 | 0 | 0 | 0 | 31s | $0.12 |
| `haiku` | 9/9 | 9/9 | 0 | 0 | 0 | 45s | $0.0094 |
| `luna` | 8/9 | 9/9 | 1 | 0 | 0 | 56s | $0.0068 |
| `gemma4-qat` | 26/27 | 27/27 | 1 | 0 | 0 | 12m 40s | $0.00 |
| `qwen3.8` | 24/27 | 22/27 | 0 | 3 | 2 | 4m 37s | $0.00 |
| `devstral` | 5/27 | 5/27 | 1 | 20 | 1 | 51s | $0.00 |
| `qwen3.6` | 0/27 | 0/27 | 0 | 27 | 0 | 19s | - |

Total cost: **$1.22**, all of it the cloud run (sonnet $1.08, haiku
$0.08, luna $0.05). The plan had estimated at most ~$14.54. No run
stopped with an error, and no cloud run needed a fix attempt.

Hidden tests passed, per task (local out of 3, cloud out of 1):

| Task | `gemma4-qat` | `qwen3.8` | `devstral` | `qwen3.6` | `haiku` | `luna` | `sonnet` |
|---|---|---|---|---|---|---|---|
| duration-parser | 3 | 3 | 0 | 0 | 1 | 1 | 1 |
| inventory-fix | 3 | 2 | 0 | 0 | 1 | 1 | 1 |
| page-ranges | 3 | 2 | 0 | 0 | 1 | 1 | 1 |
| pedestrian-crossing | 3 | 3 | 1 | 0 | 1 | 1 | 1 |
| semver-order | 3 | 3 | 0 | 0 | 1 | 1 | 1 |
| slugify | 2 | 3 | 0 | 0 | 1 | **0** | 1 |
| temperature-table | 3 | 3 | 3 | 0 | 1 | 1 | 1 |
| token-bucket | 3 | 2 | 1 | 0 | 1 | 1 | 1 |
| wordle-score | 3 | 3 | 0 | 0 | 1 | 1 | 1 |

## What the results say

- **Certo was fooled 3 times in 135 runs.** Of its 81 `verified`
  verdicts, 78 were right. All three were a rule the task stated and the
  agent's own tests didn't test (see below).
- **Weak runs were caught, not passed.** Of the 54 runs whose hidden
  tests failed, Certo said `verified` for only 3. The others ended
  `unchanged`, `inconclusive`, `incomplete`, `no_progress` or `stuck`.
- **The cloud models solved everything, cheaply.** sonnet and haiku
  passed 9 of 9; haiku did it for under a cent per task. These tasks are
  too small to separate them.
- **Two local models did the work, two mostly didn't start.**
  `gemma4-qat` and `qwen3.8` solved 50 of 54 runs between them. `qwen3.6`
  solved none and `devstral` 5, almost always because the run ended
  within a minute without any work done (see the next section).
- **`gemma4-qat` passed the most, `qwen3.8` was the best balance.** gemma4
  passed 26 of 27 but took about 12 minutes per task, almost three times
  as long as qwen3.8. qwen3.8's 3 failures were all tool calls written as
  text; it never wrote wrong code that passed, while gemma4's one failure
  was wrong code that Certo verified. The two-run difference can be
  chance.
- **Three correct local solutions ran out of time.** Two `qwen3.8` runs
  and one `devstral` run passed the hidden tests but ended
  `budget_exhausted`: they finished correct work after the 30-minute
  budget. These are the "unconfirmed passes".

## Compared with 0.1.13

| Arm | 0.1.13 | 0.1.15 |
|---|---|---|
| `sonnet` | 9/9, 37s, $1.12 | 9/9, 31s, $1.08 |
| `qwen3.8` (local) | 9/9, 6m 13s | 24/27, 4m 37s |

The 0.1.13 local run had one repeat, so 9/9 there and 24/27 here are not
a real change: with three repeats, qwen3.8's tool-call failures showed up.
0.1.13's only fooled run (no file changed) is now caught by the
`unchanged` verdict, which ended 23 runs here.

## Tool calls written as text

Every failed `qwen3.6` and `qwen3.8` run, and most failed `devstral`
runs, ended the same way. Instead of calling a tool, the model wrote the
call as plain text in its answer, for example:

```text
{"command": "view", "path": "/var/folders/.../certo-bench-5fm9iqqm"}
```

The agent framework reads a text answer as the agent's final message, so
the run ended there, before any file was written. Certo then reported
what it found: `inconclusive` (an empty folder) or `unchanged` (no file
changed, even after asking once more). Asking again didn't help, because
the model wrote its next call as text too.

| Arm | Failed runs that ended on a tool call written as text |
|---|---|
| `qwen3.6` | 27 of 27 |
| `devstral` | 18 of 22 |
| `qwen3.8` | 3 of 3 |
| `gemma4-qat` | 0 of 1 |

So these numbers measure the model **with this Ollama setup**, not the
model's coding skill. A tool-call format problem like this usually comes
from the model's chat template in Ollama, or from a context window too
small to hold the tool definitions. Which one it was here wasn't
checked. Before ruling out `qwen3.6` or `devstral`, check the setup: see
[Give the model a large enough context window](../guides/ollama-and-local-models.md#give-the-model-a-large-enough-context-window),
and run `certo check`, which fails when the model's answer doesn't come
back as a real tool call.

## The fooled runs

All three are the gap described in
[Write a task Certo can check](../guides/write-a-good-task.md#3-give-the-expected-answers-yourself):
the agent's tests share its misunderstanding.

- **`gemma4-qat` · `slugify` · repeat 3, and `luna` · `slugify`.** Two
  different models wrote the same bug. The task says: shorten a long slug
  to the longest start that ends at a word boundary and is at most
  `maxLength` long. Both cut at the last hyphen *inside* the limit, so
  when the limit fell exactly at the end of a word, they dropped that
  word: `slugify('the quick brown fox', 9)` gave `"the"`, not
  `"the-quick"`. Neither agent's tests tried a limit that lands on a
  word's end.
- **`devstral` · `semver-order` · repeat 2.** The task says: MAJOR, MINOR
  and PATCH have no leading zeros. The code rejected leading zeros in
  pre-release parts, but not in the main numbers, so `01.2.3` was
  accepted. The agent's 11 tests didn't include that case.

In each, the code passed every test the agent wrote, so `verified` was
the honest result of the checks Certo had. Catching this needs tests
written from the task by someone other than the builder, which is on the
[roadmap](https://github.com/alessioricco/certo/blob/main/ROADMAP.md).

## Reproduce this run

The two benchmark files are
[bench-0.1.15-local.yaml](bench-0.1.15-local.yaml) and
[bench-0.1.15-cloud.yaml](bench-0.1.15-cloud.yaml). Copy them, enable
their models in your `models.yaml`, and run:

```bash
certo bench --config bench-0.1.15-local.yaml
certo bench --config bench-0.1.15-cloud.yaml
```

Your numbers will differ: models vary between runs, and local times
depend on the machine serving the model.

## Limits of this baseline

- Nine small tasks. The cloud models, and the two working local models,
  solved almost all of them, so the tasks can't tell those apart.
- One repeat for the cloud models: 9 runs each.
- One Ollama setup, whose version and context length weren't recorded,
  so the tool-call failures can't yet be traced to the model or the
  setup.
- Single-model arms only: escalation wasn't measured.

## Related

- [Baseline 0.1.13](baseline-0.1.13.md)
- [Choose a local model](../guides/choose-a-local-model.md)
- [Benchmark models and strategies](../guides/benchmark.md)
- [Ollama and local models](../guides/ollama-and-local-models.md)
