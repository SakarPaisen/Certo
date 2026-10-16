# Certo v0.1.7

Continue a task after an interruption or a failed verdict.

## New

- **`certo --resume`** continues the last run in a folder (or in
  `--project NAME`) from where it stopped: after Ctrl-C, a closed
  terminal, `budget_exhausted`, `retry_exhausted` or `no_progress`. The
  agent gets its earlier conversation back, plus Certo's record of the last
  verdict and the failing checks. Add an instruction if you like:
  `certo --resume "Fix the scoring, not the test."`, or switch to a
  stronger model with `--model`.
- **A `.certo/` folder in each project** keeps that state: `STATUS.md` (the
  last run, readable by you), `run.json`, and the saved conversation. It
  ignores itself in git, so your `.gitignore` is never edited. Only the last
  run is kept. `CERTO_SAVE_STATE=0` turns it off.
- After a failing verdict, Certo prints where it stopped and the command
  to continue. Ctrl-C now exits with code 130 and the same hint, instead of
  a Python traceback.

## Good to know

- In Docker mode the conversation isn't saved: a resume starts a new
  conversation with the task, `STATUS.md` and the files.
- The saved conversation holds no API key, but it does hold everything the
  agent printed. Delete `.certo/` when you no longer need it.
- Server mode and `certo bench` don't write `.certo/`.

Guide: [Resume an interrupted run](../guides/resume-a-run.md).
