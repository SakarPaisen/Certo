# Write or contribute a benchmark task

This guide shows how to write a task for `certo bench`, check that it is
fair, and send it to the bundled task set. It is for anyone who wants to
benchmark models on their own kind of work, or help grow Certo's
benchmark. How the benchmark works is in
[Benchmark models and strategies](benchmark.md).

The bundled tasks are small. Harder tasks, with several files and
languages, are what the benchmark needs most: on today's nine tasks, a
local model and a cloud model both solved every one (see the
[0.1.13 baseline](../benchmark/baseline-0.1.13.md)).

## What a task is

A task is a folder:

```text
my-task/
  task.md        the prompt the agent sees
  starter/       optional: the files the agent starts with
  hidden_tests/  the tests that decide the score; never shown to the agent
  reference/     a solution that passes the hidden tests; never shown to the agent
```

A run copies `starter/` into an empty folder and gives the agent
`task.md`. When the agent is done, Certo copies the hidden tests into the
folder (as `.certo_hidden_tests/`) and runs them. Only the hidden tests
decide whether the task was solved. Certo's own verdict is recorded beside
it, which is how the benchmark finds runs where Certo was fooled.

## What makes a good task

- **It tests something models get wrong.** An edge case, a rule that is
  easy to misread, a fix that must not break existing behaviour. A task
  every model solves measures nothing.
- **The prompt says everything the hidden tests check**: file names,
  function names and signatures, error types, edge cases. A hidden test
  that checks something the prompt doesn't ask for measures luck.
- **It fits in one run**: a few minutes for a cloud model, within the
  30-minute time budget for a local one.
- **It is deterministic and offline**: no network, no clock, no random
  numbers without a seed, no input from a terminal.
- **It needs no packages.** Grading installs pytest for Python and nothing
  for Node, so the hidden tests and the expected solution may use only the
  standard library (Python) or Node's built-in modules.

**Languages:** grading supports Python (pytest) and Node (`node --test`)
today. Certo decides the language from the hidden test files: `.py` means
Python, `.js` means Node.

## 1. Write `task.md`

Write it as a user would, but complete. The bundled tasks are good
examples: `certo bench --list-tasks` names them, and the files are in
`src/certo/benchmark_tasks/` in a checkout. A shortened example:

```markdown
# Slugify

Write a Node.js module with no dependencies. `package.json` is already
here; keep it CommonJS and keep `npm test` running `node --test`.

## `slugify.js`

Export a function `slugify(text, maxLength = 50)` with
`module.exports = { slugify }`. It turns a title into a URL slug:

- Lower case.
- ...
- Throw a `TypeError` if `text` is not a string, and a `RangeError` if
  `maxLength` is not an integer of at least 1.

Examples: `"Hello, World!"` → `"hello-world"`;
`slugify("the quick brown fox", 12)` → `"the-quick"`.

Also write tests in `slugify.test.js`, using `node:test` and
`node:assert`.
```

- **Ask for the agent's own tests**, as the last line does. Without them
  Certo has nothing to verify, and the run tells you nothing about
  whether Certo would have been fooled.
- **Give a few examples, not the test list.** The hidden tests should
  check more cases than the prompt shows, especially the tricky ones the
  rules already describe.

The rules in [Write a task Certo can check](write-a-good-task.md) apply
here too.

## 2. Add a starter, if the task needs one

A task that fixes or extends code needs a `starter/` with that code. A
Node task needs at least a `package.json` with a `test` script, so the
agent and Certo know how the project is tested. A task that builds from
nothing in Python can leave `starter/` out.

The starter must **fail** the hidden tests: otherwise a run in which the
agent does nothing scores as solved. `--check-tasks` (step 5) checks this.

## 3. Write the hidden tests

- **Python:** pytest files (`test_*.py`) that import the solution's
  modules by name, for example `from inventory import Inventory`. They run
  with their own pytest settings, so the project's `pytest.ini` or
  `pyproject.toml` can't change how they run.
- **Node:** `*.test.js` files for `node --test`. They run from
  `.certo_hidden_tests/`, so they load the solution one folder up:
  `require('../slugify.js')`.
- **Use names the agent won't use**, such as `test_hidden_inventory.py`,
  so they never clash with the agent's own test files.
- **Test behaviour, not code.** Check results and errors through the
  public functions the prompt names, never private helpers or the exact
  wording of a message the prompt didn't fix.

## 4. Write the reference solution

`reference/` holds a correct solution. For a task with a starter, it holds
the files that change or get added; Certo copies it on top of the starter.
Include the tests the prompt asks the agent to write, so the reference is
a complete answer.

## 5. Check the task, with no model

Put your tasks in a folder of their own, point `tasks_dir` in a benchmark
file at it, and run `--check-tasks`:

```yaml
# bench-my-tasks.yaml
tasks_dir: ./my-tasks
tasks: all
repeats: 1
arms:
  - {name: local, strategy: single, model: qwen3.8-27b-local}
```

```bash
certo bench --config bench-my-tasks.yaml --check-tasks
```

It runs every task twice, with no model: the reference solution must pass
the hidden tests, and the starter alone must fail them. It ends with
`All N tasks are valid.`, or one line per broken task, and exit code 1.

## 6. Try it with real models

Run the benchmark file from step 5. Start with one repeat and one model
you can run for free; see [Write a benchmark file](write-a-benchmark-file.md).

Then read the results:

- **Every model solves it:** too easy, or the prompt gives the answer
  away. Make it harder.
- **No model solves it:** read a run's conversation in
  `runs/transcripts/<run_id>.json` in the results folder. If the agents
  misread the same sentence, the prompt is unclear; if they disagree with
  a hidden test, the test may check something the prompt doesn't say.
- **Some do, some don't:** a good task. Note which models, for the pull
  request.

## 7. Send it to the bundled set

From a checkout (see [CONTRIBUTING.md](../../CONTRIBUTING.md)):

1. Add the folder under `src/certo/benchmark_tasks/`.
2. Raise the number in `src/certo/benchmark_tasks/VERSION` by one. Any
   change to a task, even a typo in a prompt, changes the task set, and
   results are only comparable within one version.
3. Run the task tests:

   ```bash
   uv run pytest -q tests/test_bench_tasks.py
   ```

   They check every bundled task as `--check-tasks` does. One test also
   checks the size of the set (how many tasks, how many in Node); update
   it if your task changes those numbers.
4. Open a pull request that says what the task measures, why models get
   it wrong, and how the models you tried did (step 6), ideally at least
   one local and one cloud model.

## Related

- [Benchmark models and strategies](benchmark.md): what the benchmark
  measures and how to read the results.
- [Write a benchmark file](write-a-benchmark-file.md)
- [bench.yaml reference](../reference/bench-yaml.md): `tasks_dir` and
  every other key.
- [Commands: certo bench](../reference/commands.md#certo-bench):
  `--check-tasks` and `--list-tasks`.
