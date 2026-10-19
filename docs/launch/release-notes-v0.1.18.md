# Certo v0.1.18

A run now starts with a banner. This release also contains
[v0.1.17](release-notes-v0.1.17.md) and the unpublished versions before
it.

## New: a banner at the start of every run

`certo "<task>"` now prints its version and the settings that decide how
the run goes, before the agent starts:

```text
── Certo 0.1.18 ────────────────────────────────────────────
  Model    openai/gpt-5.6-luna
  Folder   /home/you/certo-workspace/projects/wordle (project wordle)
  Runs on  this computer
  Checks   on, up to 2 fix attempts
  Limits   30 min · 50 steps
────────────────────────────────────────────────────────────
```

If the model or the folder is not the one you meant, stop the run with
Ctrl-C before it spends anything. With `--escalate`, the model line shows
the ladder; with `--auto-model`, that the model is picked for the task.
The API key is never shown. See
[Commands](../reference/commands.md#certo).

## Changed: no more `Project workspace:` line

With `--project`, the folder is now in the banner, so the separate
`Project workspace: <path>` line is gone. If a script of yours read that
line, read the banner's `Folder` line instead.
