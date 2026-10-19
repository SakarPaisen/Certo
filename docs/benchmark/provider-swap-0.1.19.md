# Provider swap in Certo 0.1.19

One task, run twice with the same command. Between the two runs only
`CERTO_LLM_MODEL` and the key changed: an OpenAI model, then an Anthropic
model. No code, no other setting. It checks Certo's main promise about
models: switching provider is a settings change, never a code change.

This is two single runs, not a benchmark. It shows that the swap works,
not which model is better. For that, see
[Baseline 0.1.15](baseline-0.1.15.md).

## The setup

- **Certo:** 0.1.19, from a source checkout. **Run:** 2026-10-19, both
  runs started at 13:28 UTC, each in its own new, empty folder.
- **Machine:** Darwin 25.6.0, arm64, Apple M1, 16 GB RAM.
- **Settings:** the defaults. Checks on, up to 2 fix attempts, 30 minutes
  and 50 steps.

The two commands, with the key left out:

```bash
CERTO_LLM_MODEL=openai/gpt-5.6-luna CERTO_LLM_API_KEY=... certo task.md
CERTO_LLM_MODEL=anthropic/claude-haiku-5-5 CERTO_LLM_API_KEY=... certo task.md
```

The task, `task.md`:

```text
Write a small Python module `roman.py` with two functions:

- `to_roman(n: int) -> str` converts 1..3999 to a Roman numeral (e.g. 1994 -> "MCMXCIV").
- `from_roman(s: str) -> int` converts back, accepting upper-case numerals only.

Both raise `ValueError` for anything out of range or invalid (0, 4000, "IIII", "ABC", "").

Add pytest tests in `test_roman.py` covering normal values, the round trip for every number from 1 to 3999, and the errors. Add a short README.md saying how to run the tests.
```

## Results

| Model | Verdict | Time | Tokens | Cost | Its own tests |
|---|---|---|---|---|---|
| `openai/gpt-5.6-luna` | `verified` | 46.4s | 77,129 | $0.0090 | 23 passed |
| `anthropic/claude-haiku-5-5` | `verified` | 55.9s | 133,346 | $0.0083 | 39 passed |

Both banners showed the model that was set, and nothing else changed:

```text
── Certo 0.1.19 ────────────────────────────────────────────
  Model    anthropic/claude-haiku-5-5
  Folder   .../m3/anthropic
  Runs on  this computer
  Checks   on, up to 2 fix attempts
  Limits   30 min · 50 steps
────────────────────────────────────────────────────────────
```

`certo verify` run afterwards on each folder, with no model, also gave
`verified`.

## Each model's tests on the other's code

A `verified` verdict means the project's own tests pass. Those tests were
written by the same model, so as an extra check each model's tests were
run against the other model's `roman.py`:

| Tests from | Code from | Result |
|---|---|---|
| Claude Haiku | GPT-5.6 Luna | 39 passed |
| GPT-5.6 Luna | Claude Haiku | 19 passed, 4 failed |

The 4 failures are about input of the wrong type, such as a float or a
number given as a string. GPT-5.6 Luna's tests expect `ValueError`;
Claude Haiku's code raises `TypeError`. The task names `ValueError` only
for values out of range or invalid, not for the wrong type, so both
readings fit the task. Every case the task lists passed both ways.

This is the limit of verifying with the agent's own tests: they check
what the agent understood. [How verification works](../concepts/how-verification-works.md)
says more.
