# Four local models: Certo 0.1.15

A `certo bench` run of four local models, each alone, on the 9 bundled
tasks, three times each. It answers two questions: which local model to
start with, and how often Certo was fooled when the model was weak. How
the benchmark works, and what each column means, is in
[Benchmark models and strategies](../guides/benchmark.md).

## The setup

- **Certo:** 0.1.15. **Task set:** version 1 (`11b1105b535e`, bundled),
  9 tasks: 6 Python, 3 Node.
- **Date:** 2026-10-18, 08:14 to 19:55 UTC.
- **Machine running Certo:** Darwin 25.6.0, arm64, Apple M1, 8 CPUs,
  16 GB RAM. The models ran on Ollama on another machine. Its Ollama
  version and context length weren't recorded, so the times are only
  comparable with each other.
- **Repeats:** 3. Each model has 27 runs.

| Arm | Model |
|---|---|
| `qwen3.8` | `ollama/qwen3.8:27b` |
| `qwen3.6` | `ollama/qwen3.6:35b-a3b` |
| `devstral` | `ollama/devstral-small-2:24b` |
| `gemma4-qat` | `ollama/gemma4:31b-it-qat` |

## Results

| Arm | Hidden tests passed | Verified | Fooled | Caught | Unconfirmed passes | Median time |
|---|---|---|---|---|---|---|
| `gemma4-qat` | **26/27** | 27/27 | 1 | 0 | 0 | 12m 40s |
| `qwen3.8` | 24/27 | 22/27 | 0 | 3 | 2 | 4m 37s |
| `devstral` | 5/27 | 5/27 | 1 | 20 | 1 | 51s |
| `qwen3.6` | 0/27 | 0/27 | 0 | 27 | 0 | 19s |

Every run cost $0.00. All 108 runs finished with a verdict; none stopped
with an error.

Hidden tests passed, per task (out of 3):

| Task | `gemma4-qat` | `qwen3.8` | `devstral` | `qwen3.6` |
|---|---|---|---|---|
| duration-parser | 3 | 3 | 0 | 0 |
| inventory-fix | 3 | 2 | 0 | 0 |
| page-ranges | 3 | 2 | 0 | 0 |
| pedestrian-crossing | 3 | 3 | 1 | 0 |
| semver-order | 3 | 3 | 0 | 0 |
| slugify | 2 | 3 | 0 | 0 |
| temperature-table | 3 | 3 | 3 | 0 |
| token-bucket | 3 | 2 | 1 | 0 |
| wordle-score | 3 | 3 | 0 | 0 |

## What the results say

- **Two models did the work, two mostly didn't start.** `gemma4-qat` and
  `qwen3.8` solved 50 of 54 runs between them. `qwen3.6` solved none and
  `devstral` 5, almost always because the run ended within a minute
  without any work done (see the next section).
- **`gemma4-qat` was the most accurate, `qwen3.8` the best balance.**
  gemma4 passed 26 of 27 runs but took about 12 minutes per task, almost
  three times as long as qwen3.8. qwen3.8 passed 24 of 27 in under 5
  minutes per task.
- **Certo was fooled twice in 108 runs**, both times on a rule the task
  stated and the agent's own tests didn't test (see below). Of the 54
  `verified` verdicts, 52 were right.
- **Weak runs were caught, not passed.** Of the 53 runs whose hidden
  tests failed, Certo said `verified` for only 2. The others ended
  `unchanged`, `inconclusive`, `incomplete`, `no_progress` or `stuck`.
- **Three correct solutions ran out of time.** Two `qwen3.8` runs and one
  `devstral` run passed the hidden tests but ended `budget_exhausted`:
  they finished correct work after the 30-minute budget. These are the
  "unconfirmed passes".

## Tool calls written as text

Every failed `qwen3.6` and `qwen3.8` run, and most failed `devstral`
runs, ended the same way. Instead of calling a tool, the model wrote the call as plain
text in its answer, for example:

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

Both are the gap described in
[Write a task Certo can check](../guides/write-a-good-task.md#3-give-the-expected-answers-yourself):
the agent's tests share its misunderstanding.

- **`gemma4-qat` · `slugify` · repeat 3.** The task says: shorten a long
  slug to the longest start that ends at a word boundary and is at most
  `maxLength` long. The code cut at the last hyphen *inside* the limit, so
  when the limit fell exactly at the end of a word, it dropped that word:
  `slugify('the quick brown fox', 9)` gave `"the"`, not `"the-quick"`.
  The agent's own tests never tried a limit that lands on a word's end.
- **`devstral` · `semver-order` · repeat 2.** The task says: MAJOR, MINOR
  and PATCH have no leading zeros. The code rejected leading zeros in
  pre-release parts, but not in the main numbers, so `01.2.3` was
  accepted. The agent's 11 tests didn't include that case.

In both, the code passed every test the agent wrote, so `verified` was
the honest result of the checks Certo had. Catching this needs tests
written from the task by someone other than the builder, which is on the
[roadmap](https://github.com/alessioricco/certo/blob/main/ROADMAP.md).

## Limits of this run

- Nine small tasks, local models only, one Ollama setup.
- The Ollama server's version and context length weren't recorded, so
  the tool-call failures can't yet be traced to the model or the setup.
- Single-model arms only: no escalation.

## Related

- [Baseline 0.1.13](baseline-0.1.13.md): the first complete benchmark,
  with a cloud model.
- [Benchmark models and strategies](../guides/benchmark.md)
- [Ollama and local models](../guides/ollama-and-local-models.md)
