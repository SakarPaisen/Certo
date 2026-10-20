# Certo v0.1.21 (not released yet)

This release is about the first hour with Certo, from a walk-through as
a new user:

- **Setting up:** `certo init` asks with arrow-key menus, offers DeepSeek
  and Kimi, and can run your first task at the end. `certo init models`
  sets up more than one model without editing a file, and `certo models
  update` keeps your list of models up to date. Keys stay in one place,
  your settings file.
- **Running:** a run prints a third of what it did, and Certo's own notes
  show as they happen.

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

## New: `certo init models`

More than one model, for `--auto-model` and `--escalate`, no longer means
copying three example files and editing YAML. `certo init models` starts
from the model `certo init` saved and offers the models this computer can
reach: the Ollama models on your server, the cloud models whose key you
have, a key for another provider (asked hidden, saved only in your
settings file), or any other LiteLLM model id. It tests each chosen model
with one small request, writes only the ones that pass, shows what
`--auto-model` and `--escalate` would do with them, and asks which mode
to use for every run, with one model as the default. A model that isn't
in Certo's list is rated by you, next to the list's ratings of the
models you chose. See [Commands](../reference/commands.md#certo-init-models).

## New: `certo init` can run your first task

When the model check passes, `certo init` now ends by offering to run the
sample task (a Wordle game) right away, so a new user sees a first
verdict without typing another command. It says how long that takes and,
for a cloud model, that it uses your credits. **Not now** prints the
command for later, as before.

## New: arrow-key menus in `certo init`

On a terminal, `certo init` and `certo init models` now ask with menus:
↑↓ and Enter to choose, and in `certo init models` a checklist where
Space turns a model on or off. The Ollama model menu also has **Another
model**, to type one that isn't installed yet. Without a full terminal
(output piped, or `TERM=dumb`), the questions are numbered, as before.

## New: `certo models update`

Your `models_list.yaml` is a copy of the example list, and a Certo release
can update the example: new models, new ratings. `certo models update`
compares your copy with the example it came from and the new one, offers
Certo's changes (all, one by one, or none) and keeps yours: a model you
added, a rating you changed. An entry both changed is asked about. Your
comments stay, and the old file is kept as `models_list.yaml.bak`. See
[Commands](../reference/commands.md#certo-models-update).

## New: DeepSeek and Kimi in `certo init`

`certo init` now offers DeepSeek (`deepseek/deepseek-flash`) and Kimi
from Moonshot AI (`moonshot/kimi-k2.7-code`) by name, and reuses
`DEEPSEEK_API_KEY` or `MOONSHOT_API_KEY` when you have exported one.
Before, both needed **Other** and a typed model id. With DeepSeek, the
run summary may show the cost as unknown, because LiteLLM's price list
doesn't know the name `deepseek-flash` yet. See
[OpenAI, Claude and Gemini](../guides/openai-claude-gemini.md).

## New: keys in one place, with `${NAME}` in `models.yaml`

`models.yaml` can now name a key instead of holding it:

```yaml
models:
  - name: claude-haiku-5-5
    api_key: "${ANTHROPIC_API_KEY}"
```

The key itself goes in your settings file, as `ANTHROPIC_API_KEY=...`,
so each key is in one place. `base_url` can use `${NAME}` too. Before,
`${NAME}` was sent to the provider as written, which is a rejected key.
When the variable isn't set, the model is now left out and Certo says
which variable is missing. The example `models.yaml` uses this form. See
[The model files](../reference/models-yaml.md#modelsyaml).

## Fixed: `certo --escalate "task"` runs the task

`--escalate` takes an optional ladder name, so with the flag before the
task, Certo read the task as the ladder's name and stopped with "the
following arguments are required: task". Now a single value after
`--escalate` is the task, on the default ladder, as the docs showed.
`certo --escalate hard "task"` still uses the ladder named `hard`. See
[Commands](../reference/commands.md#certo).
