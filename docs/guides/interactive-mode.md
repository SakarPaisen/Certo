# Interactive and confirm mode

By default, Certo's agent works alone from start to finish. This guide
shows the two ways to stay involved: answering the agent's questions
(interactive mode) and approving every action before it runs (confirm
mode). Both work only in the `certo` command, not in server mode.

## Why the agent doesn't ask by default

The agent is told that nobody is available to answer questions, so it
should decide for itself and keep working until the task is done. This is
on purpose: the tool Certo is built on can't tell a question from a final
answer. Without this rule, an agent that stops to ask "should I use SQLite
or Postgres?" would look exactly like an agent that finished.

## Interactive mode: answer the agent

```bash
certo "Scaffold a FastAPI service" --project my-api --interactive
```

Or set `CERTO_INTERACTIVE=yes` in your settings.

- The agent may stop and ask instead of guessing.
- When it stops, Certo shows its last message and asks you:

  ```text
  Your reply (Enter to finish the task):
  ```

  Type an answer to continue the same conversation, or press Enter to
  accept the work as done.
- You can go back and forth as many times as you want.
- Time spent waiting for you doesn't count against the task's time budget.

**Only the first part of the task is interactive.** After you press Enter,
Certo's own checks run as usual: if a test fails, Certo sends the failure
back to the agent and lets it retry with no further questions to you.

With `--auto-model` too, Certo also shows the ranked model list and lets
you pick one. See [Pick models automatically](pick-models-automatically.md).

## Confirm mode: approve every action

Set this in your settings (there is no command-line flag):

```bash
CERTO_CONFIRM_MODE=always
```

Before every action, such as a terminal command or a file edit, Certo
shows it and waits:

```text
--- Confirmation required (CERTO_CONFIRM_MODE=always) ---
  terminal: command='rm -rf build/' is_input=False timeout=None reset=False kind='TerminalAction'
Approve? [y/N]
```

- Only `y` or `yes` approves. Anything else, including just Enter, rejects
  the action. The agent sees the rejection and can try something else.
- Approving lets exactly that one action run. The agent asks again before
  the next one.

Confirm mode is slow for long tasks, but useful when you try a new model,
a new skill, or a task on an important folder.

## In server mode

The server has no terminal to ask you, so:

- `CERTO_INTERACTIVE=yes` only removes the "work alone" rule. Nobody can
  answer, so tasks may end less complete. Leave it at `no` for
  `certo-server`.
- With `CERTO_CONFIRM_MODE=always`, the first action is rejected and the
  task stops with the verdict `confirmation_required`. Leave it at `never`
  for `certo-server`.

## Related

- [Safety](../concepts/safety.md)
- [Commands](../reference/commands.md#certo)
