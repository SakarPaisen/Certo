# Certo v0.1.6

Measure which models really deliver, with tests the agent never sees.

## New

- **`certo bench`, a benchmark.** It runs the normal Certo pipeline on a
  set of small coding tasks, for every model you compare, and grades each
  result with **hidden tests**: tests written with the task and never
  shown to the agent. It reports, per model:
  - how often the hidden tests passed (`passed/total` and a percentage);
  - how often Certo said `verified`;
  - how often Certo was **fooled** (it said `verified`, the hidden tests
    failed), and how often it **caught** a false "done" (the agent claimed
    it was done, Certo didn't say `verified`);
  - time, tokens and cost.
- **Nine bundled tasks** (task set version 1): six Python, three Node,
  from easy to tricky: an inclusive range, Wordle scoring with repeated
  letters, a traffic-light state machine, duration parsing, print page
  ranges, fixing existing code, slugs, a rate limiter with a fake clock,
  and version ordering. `certo bench --list-tasks` shows them.
- **Models come from `models.yaml`, by name.** A new `bench.yaml` says
  which entries to compare and how many times. It holds no keys and never
  touches `.env`. Copy `bench.yaml.example` to start.
- **Every run is isolated**: a fresh folder with only the task's starter
  files, and Certo's default limits and built-in skills.
- **Safe to leave running.** The plan and a rough cost estimate come
  first, with a confirmation (or `--yes`). `--max-cost` stops starting new
  runs at a spending cap. An interrupted benchmark keeps its runs, and
  `--resume` continues it. `--parallel N` speeds up cloud-only
  benchmarks.
- **Results to read and share**: `results.md` (with the Certo version,
  hardware, task set and models in the header), `results.csv`, the JSON of
  every run, and the code each run left behind.
- **Your own tasks**: point `tasks_dir` at a folder in the same shape, and
  check it with `certo bench --check-tasks`, no model needed.

## Good to know

- `certo bench` is a subcommand only as the whole first argument, like
  `verify`, `init` and `check`. To run the one-word task "bench", write
  `certo -- bench`.
- A first run of the benchmark already found a gap in Certo: a Node
  project whose `test` script finds no test files (`node --test` with no
  tests) counts as `verified`. It is documented in
  [Verification by language](../reference/verification-by-language.md#node-in-detail),
  and the benchmark counts such runs as "fooled".

Guide: [Benchmark models and strategies](../guides/benchmark.md).
