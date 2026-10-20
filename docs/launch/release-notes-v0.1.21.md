# Certo v0.1.21 (not released yet)

A run prints a third of what it did, Certo's own notes now show as they
happen, and `certo init` offers DeepSeek and Kimi.

## Changed: a quieter run

A run printed the agent's whole system prompt and the whole task with the
skills Certo adds, both before the agent's first step, plus the SDK's own
logs and the agent's last message twice. Certo's own notes, such as a
model switch or a failing check, were lost among them. On a first Wordle
run with `qwen3.8:27b`, that was 2,949 lines. Now:

- the system prompt and the task are one line each:

  ```text
  System prompt: 270 lines (--verbose shows it)
  Task: Wordle in the terminal (210 lines with the skills; --verbose shows them)
  ```

- the SDK's `INFO` logs are hidden (warnings still show; the SDK's own
  `LOG_LEVEL`, when you set it, still applies);
- Certo's notes are printed as they happen;
- the agent's last message is printed once.

The same run now prints 1,021 lines, with every step of the agent still
shown. `--verbose` (or `CERTO_VERBOSE=yes`) prints everything as before.
See [Commands](../reference/commands.md#certo) and
[Configuration](../reference/configuration.md).

## New: DeepSeek and Kimi in `certo init`

`certo init` now offers DeepSeek (`deepseek/deepseek-flash`) and Kimi
from Moonshot AI (`moonshot/kimi-k2.7-code`) by name, and reuses
`DEEPSEEK_API_KEY` or `MOONSHOT_API_KEY` when you have exported one.
Before, both needed **Other** and a typed model id. With DeepSeek, the
run summary may show the cost as unknown, because LiteLLM's price list
doesn't know the name `deepseek-flash` yet. See
[OpenAI, Claude and Gemini](../guides/openai-claude-gemini.md).

## Fixed: `certo --escalate "task"` runs the task

`--escalate` takes an optional ladder name, so with the flag before the
task, Certo read the task as the ladder's name and stopped with "the
following arguments are required: task". Now a single value after
`--escalate` is the task, on the default ladder, as the docs showed.
`certo --escalate hard "task"` still uses the ladder named `hard`. See
[Commands](../reference/commands.md#certo).
