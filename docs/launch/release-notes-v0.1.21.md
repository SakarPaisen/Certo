# Certo v0.1.21 (not released yet)

## Fixed: `certo --escalate "task"` runs the task

`--escalate` takes an optional ladder name, so with the flag before the
task, Certo read the task as the ladder's name and stopped with "the
following arguments are required: task". Now a single value after
`--escalate` is the task, on the default ladder, as the docs showed.
`certo --escalate hard "task"` still uses the ladder named `hard`. See
[Commands](../reference/commands.md#certo).
