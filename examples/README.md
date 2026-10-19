# Examples

Task files to try Certo on, and a script that runs one task with several
models so you can compare them.

## Task files

Each file is a task description you can give to Certo as it is:

| File | What it asks for |
|---|---|
| `asteroids.md` | An asteroid-dodging arcade game for the browser, in JavaScript |
| `hanoi.md` | A Tower of Hanoi game in the terminal, in Python |
| `invaders.md` | A Space Invaders–style game for the browser, in JavaScript |
| `mazeman.md` | A maze-chase arcade game for the browser |

The browser games need Node 18 or newer.

```bash
certo examples/hanoi.md --project hanoi
```

## Compare models on the same task

`compare-models.sh.example` runs one task with every model in a list, one
after the other. Each model builds its own copy of the project, so you
can look at the results side by side, and the script ends with a summary
table:

```text
| Model | Verdict | Time | Cost | Exit |
|---|---|---|---|---|
| `anthropic/claude-haiku-5-5` | verified | 27.6s | $0.0053 | 0 |
| `openai/gpt-5.6-luna` | verified | 36.2s | $0.0077 | 0 |
| `gemini/gemini-3.8-flash` | skipped: GEMINI_API_KEY not set | | | |
```

That table is from a real run, on a small task (a leap-year function with
tests).

### 1. Copy the script

The `.example` file is the template; your copy is the one you edit:

```bash
cp examples/compare-models.sh.example compare-models.sh
chmod +x compare-models.sh
```

### 2. Choose the models

Open `compare-models.sh` and edit the lines between the two `# ----`
markers. One line is one model:

```bash
run anthropic/claude-sonnet-5-5   ANTHROPIC_API_KEY
run openai/gpt-5.6-luna           OPENAI_API_KEY
run ollama/qwen3.8:27b            ""  http://localhost:11434
```

Each line has:

1. **The model**, as a [LiteLLM model id](https://docs.litellm.ai/docs/providers),
   the same value you would put in `CERTO_LLM_MODEL`.
2. **The name of the environment variable that holds its key**, such as
   `ANTHROPIC_API_KEY`. Write the variable's *name*, never the key itself.
   For a local model, write `""`.
3. **The server address**, only for a local or self-hosted model.

Delete the lines you don't need and add as many as you like. A line whose
key variable isn't set is skipped, and the summary says so.

### 3. Set the keys

Export each key in the shell you run the script from:

```bash
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
```

The script passes each key to Certo in the environment, never on the
command line, so it doesn't appear in the process list or in a log.

### 4. Run it

Pass the task file:

```bash
./compare-models.sh examples/hanoi.md
```

Everything goes in a new folder, `./compare-results/<task>-<date>-<time>/`:

- `projects/<model>/`: the project each model built;
- `<model>.log`: everything Certo printed for that model;
- `summary.md`: the summary table.

From a source checkout of Certo, use the checkout's version:

```bash
CERTO="uv run certo" ./compare-models.sh examples/hanoi.md
```

`OUT=folder` changes where the results go.

### Good to know

- **The models run one after the other**, not at the same time, so the
  times are comparable and a local model has the machine to itself.
  Expect minutes per cloud model, and more for a local one.
- **Cloud models cost money.** Each run prints its cost, and the summary
  repeats it. The game tasks in this folder are bigger than the leap-year
  example above; try one cheap model first.
- **Each line runs on its own settings.** The script sets the model, the
  key and the server address for each run, so the model in your `.env`
  doesn't matter. Your other settings (time budget, fix attempts) still
  apply to every run.
- **One run per model is one sample.** Models vary from run to run. To
  compare models properly, with hidden tests and repeats, use
  [`certo bench`](../docs/guides/benchmark.md).
