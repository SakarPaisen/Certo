# Certo v0.1.13

`certo bench` now keeps what it really spent. This release also contains
[v0.1.12](release-notes-v0.1.12.md) and [v0.1.11](release-notes-v0.1.11.md),
which were not published on their own.

## New: the real cost, next to the estimate

At the end of a benchmark, Certo prints the total it really spent and what
the plan estimated:

```text
Total cost: $1.5000 (the plan estimated at most ~$9.00, likely ~$3.50), for 3 of 12 runs
```

The same goes into the results folder:

- **`results.md`** has a new **Cost** section: the total, and one row per
  model with its runs, its cost and its average per run. An escalation run
  is split by rung, so each model is charged only for what it ran.
- **`cost.json`** (new) holds the same numbers for scripts.
- **`meta.json`** keeps the plan's estimate from when the benchmark
  started.

## Good to know

- Costs come from LiteLLM's prices; `+ unknown` means a model had no price.
- A results folder from an older version has no stored estimate, so only
  the real cost is shown. `--resume` works as before.
