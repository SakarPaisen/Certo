# Certo v0.1.15

`certo bench` keeps each run's whole conversation. This release also
contains [v0.1.14](release-notes-v0.1.14.md) and the unpublished versions
before it.

## New: a transcript for every benchmark run

Each run now writes `runs/transcripts/<run>.json` in the results folder:
the agent's messages, the tools' output and Certo's own notes, in order.
When a run ends unexpectedly, for example a `fooled` run, the transcript
shows what the agent did.

## Good to know

- A transcript holds every tool output, so a long run's file can be large.
- A results folder from an older version has no transcripts. `--resume`
  works as before; only the new runs get one.
