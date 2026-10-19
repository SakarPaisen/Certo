# Certo v0.1.20 (not released yet)

## Fixed: `--auto-model` reads the task's title, not its whole text

`--auto-model` picks a task profile by looking for trigger words in the
task. It used to search the whole text, including inside longer words, so
almost every task file matched the `debugging` profile of the example
catalog: a spec that says "raise ValueError" contains "error", and "fix
all build failures" contains "fix". With the shipped example catalog, 12
of the 14 task files Certo ships were classified as debugging.

Now Certo looks only at the task's first line with text (a task file's
title, or the whole task when it is one line), and a trigger must be a
whole word, or its plural: "bug" matches "bugs", "fix" no longer matches
"prefix". `MODEL_DECISIONS.md` says which word matched. If your own task
profiles relied on words in the body of a task, put them in its title.
See [Pick models automatically](../guides/pick-models-automatically.md).
