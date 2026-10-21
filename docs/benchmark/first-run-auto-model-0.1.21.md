# First run with two models in Certo 0.1.21

How long a new user waits from installing Certo to a first `--auto-model`
run that ends `verified`, with no file edited by hand: every choice is
made in `certo init` and `certo init models`. One run, not a benchmark.
The one-model first run is in [First run in 0.1.19](first-run-0.1.19.md).

## The setup

- **Certo:** 0.1.21, installed from PyPI.
- **Machine:** Darwin 25.6.0, arm64, Apple M1, 16 GB RAM, home internet.
  Python 3.12, uv and Node were already installed.
- **A new user:** an empty home folder and an empty uv cache, so every
  package was downloaded. The menus ran in a pseudo-terminal, driven by a
  script that answered each question as soon as it appeared, so the times
  leave out a person's reading and thinking.
- **Run:** 2026-10-21.

The steps:

```bash
uv tool install certo
certo --version
certo init
certo init models
cd certo-workspace
certo --auto-model tasks/wordle.md --project wordle
```

The answers:

- **`certo init`:** Anthropic (Claude), the default model
  (`anthropic/claude-sonnet-5-5`), the key typed at the hidden prompt,
  settings for all projects, the sample folder, then **Not now** in the
  sample menu.
- **`certo init models`:** Claude Haiku 5.5 added to the model already
  set up, then `--auto-model` as the mode for every run.

## Results

| Step | Time | Result |
|---|---|---|
| `uv tool install certo` | 8.5s | 3 commands installed |
| `certo --version` | 15.0s | `certo 0.1.21` |
| `certo init` | 14.2s | settings saved, model check `ok` |
| `certo init models` | 11.6s | both models `ok`, `CERTO_MODEL_SELECTION=auto` saved |
| `certo --auto-model tasks/wordle.md --project wordle` | 1m 52.6s | `verified`, $0.0180 |
| **Total** | **2m 41.9s** | |

`--auto-model` sorted the task into the `default` profile and chose
`claude-haiku-5-5` (score 22, against 19 for `claude-sonnet-5-5`). The task
itself ran for 1m 47s and used 465,187 tokens, 405,179 of them cached.

## What a new user notices

- **No file to edit.** The key is typed once, at a hidden prompt, and
  stays in the settings file; `models.yaml` names it as
  `${CERTO_LLM_API_KEY}`. Before 0.1.21, a second model meant writing
  `models.yaml` by hand.
- **The choice is shown before any run.** `certo init models` ends with
  the model each kind of task would get, and the order `--escalate` would
  climb, so the user sees what `--auto-model` will do.
- **The first command is still slow.** The first `certo --version` took
  15.0s while Python compiled Certo and its libraries.
- **One warning in this run:** "your terminal doesn't support cursor
  position requests (CPR)". It comes from the pseudo-terminal the script
  used, which doesn't answer that request.
