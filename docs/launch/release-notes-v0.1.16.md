# Certo v0.1.16

Escalation now moves on when a model did no work at all. This release
also contains [v0.1.15](release-notes-v0.1.15.md) and the unpublished
versions before it.

## Changed: a model that wrote no file climbs to the next one

With `--escalate`, a rung that ends `inconclusive` used to stop the climb:
nothing could be checked, so a stronger model would face the same blank.
That is still true when the model wrote files. But in Certo's 0.1.15
benchmark, some local models wrote their tool calls as text, and the run
ended at once with an empty folder. A stronger model could have done the
task, and was never asked.

Now an `inconclusive` rung that created, changed or deleted no file
climbs to the next model, like `unchanged` does. The next model is told
that no file was written. Two rungs in a row that changed no file still
stop the climb, whatever their verdicts.

See [What makes Certo climb](../guides/escalate-between-models.md#what-makes-certo-climb).

## Good to know

- An `inconclusive` rung that did write files stops the climb, as before.
- Without `--escalate`, nothing changes: a single-model run that writes no
  file still ends `inconclusive`.
