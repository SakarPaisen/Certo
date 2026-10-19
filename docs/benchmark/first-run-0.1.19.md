# First run in Certo 0.1.19

How long a new user waits from installing Certo to the first `verified`
project, following [Getting started](../getting-started.md) with a cloud
model. One run, not a benchmark.

## The setup

- **Certo:** 0.1.19, installed from a wheel built from the source
  checkout (the same files a PyPI install gets).
- **Machine:** Darwin 25.6.0, arm64, Apple M1, 16 GB RAM, home internet.
  Python and uv were already installed.
- **A new user:** an empty home folder and an empty uv cache, so every
  package was downloaded. The Anthropic key was in `ANTHROPIC_API_KEY`.
- **Run:** 2026-10-19.

The steps, as in Getting started:

```bash
uv tool install certo
certo --version
certo init --provider anthropic --yes
cd certo-workspace
certo tasks/wordle.md --project wordle
```

## Results

| Step | Time | Result |
|---|---|---|
| `uv tool install certo` | 11.4s | 3 commands installed |
| `certo --version` | 18.6s | `certo 0.1.19` |
| `certo init` | 5.7s | settings saved, model check `ok` |
| `certo tasks/wordle.md --project wordle` | 52.8s | `verified`, $0.1334 |
| **Total** | **88.5s** | |

The model was `anthropic/claude-sonnet-5-5`, the default `certo init`
picks for Anthropic. The task itself ran for 48.5s and used 120,901
tokens.

## What a new user notices

- **The first command is slow.** The first `certo --version` took 18.6s:
  Python compiles Certo and its libraries the first time they load. Later
  runs took about 3s. `uv tool install --compile-bytecode certo` moves
  that work into the install.
- **The output is long.** After the banner, the run prints the agent's
  full instructions (about 500 lines) and the first message with the
  task (about 500 more) before the agent's first step. The verdict and
  the run summary are at the end.
