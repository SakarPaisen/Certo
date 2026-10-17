# Certo v0.1.12

A truer cost estimate for escalation in `certo bench`. This release also
contains everything in [v0.1.11](release-notes-v0.1.11.md), which was not
published on its own.

## Fixed: a derived escalate arm was priced on every active model

A `strategy: escalate` arm with no `models:` uses the ladder Certo derives
from the ratings, which has at most `max_rungs` rungs (3 by default). The
plan priced it as if every active model could run: on a real file, $58.95
for the arm instead of $24.30. The plan now shows and prices only the
derived ladder, and says it is the same for every task.

## New: "likely" next to "at most"

An escalation run usually stops before the top rung, so the old estimate
(every rung runs) is the most it can cost, not what it will probably cost.
The plan now says so, and adds a likely cost when earlier results in the
same parent folder (`bench-results/` by default) cover the lower rungs:

```text
  Estimated cost: at most ~$22.00, likely ~$6.00 (rough: assumes ~500k input and ~20k output tokens per run)
```

Each rung's cost is weighted by the share of earlier runs that climbed past
the rungs below it. With no history, only "at most" is shown, and the plan
names the models that have none.

## Good to know

- The estimate still assumes about 500k input and 20k output tokens per
  run. `--max-cost` works on the recorded cost, not on the estimate.
- A model's history counts only under the same model id: change the id of
  an entry and its history starts over.
