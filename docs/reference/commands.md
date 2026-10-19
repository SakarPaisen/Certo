# Commands

Every command, subcommand and flag Certo installs. It is for looking
things up; for a walk-through, see [Getting started](../getting-started.md).

Certo installs three commands: `certo`, `certo-server` and `certo-admin`.
`certo` also has four subcommands: `certo verify`, `certo init`,
`certo check` and `certo bench`. Every command and subcommand accepts `-h` / `--help`.

All three commands hide the OpenHands SDK's start-up banner. Set
`OPENHANDS_SUPPRESS_BANNER=0` to see it.

## `certo`

Run a task through the agent, then verify the result.

```text
certo TASK [--project NAME] [--execution {local,docker}] [--model MODEL]
           [--api-key KEY] [--base-url URL] [--reasoning-effort LEVEL]
           [--agents-md TEXT] [--interactive] [--auto-model]
           [--require-verification] [--acceptance-checks JSON_OR_FILE]
           [--escalate [LADDER]]
certo --resume [TASK] [same options]
```

**`TASK`** (required, except with `--resume`) is one of, checked in this order:

1. an `http://` or `https://` URL: the page is downloaded (15-second
   limit) and used as the task;
2. the path of an existing file: the file is read (UTF-8);
3. anything else: the text itself is the task.

An empty file or page is an error. Only `http` and `https` URLs are
fetched. Note: if your task text is exactly the name of a file in the
current folder, the file is read instead.

| Flag | Default | Effect |
|---|---|---|
| `--version` | | Print the version, e.g. `certo 0.1.5`, and exit. |
| `--project NAME` | none | Work in `CERTO_PROJECTS_DIR/NAME`, created if missing. Without it, Certo works in `CERTO_WORKSPACE` (default: the current folder). `NAME` must be a relative path with no `..`, and must stay inside `CERTO_PROJECTS_DIR`. |
| `--execution {local,docker}` | `CERTO_EXECUTION` | Where the agent's tools run, for this run. `docker` is [experimental](../README.md#experimental-features). See [Run in Docker](../guides/run-in-docker.md). |
| `--model MODEL` | `CERTO_LLM_MODEL` | Model for this run only. |
| `--api-key KEY` | `CERTO_LLM_API_KEY` | API key for this run only. It ends up in your shell history. |
| `--base-url URL` | `CERTO_LLM_BASE_URL` | Server address for this run only. |
| `--reasoning-effort LEVEL` | `CERTO_LLM_REASONING_EFFORT` | Reasoning effort for this run only: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, or any value the provider accepts. `none` or `off` turns it off. |
| `--agents-md TEXT` | none | Write `TEXT` as the project's `AGENTS.md` before the task. Needs `--project`. |
| `--interactive` | off (`CERTO_INTERACTIVE`) | Let the agent stop and ask you questions. See [Interactive and confirm mode](../guides/interactive-mode.md). |
| `--auto-model` | off (`CERTO_MODEL_SELECTION`) | Pick the model from the model files (`models_list.yaml`, `models.yaml`, and the task profiles in `task_profiles.yaml`). See [Pick models automatically](../guides/pick-models-automatically.md). |
| `--require-verification` | off | Exit 1 for `inconclusive` and `unchanged` too. |
| `--acceptance-checks JSON_OR_FILE` | none | Extra file checks for this task, as inline JSON or a JSON file. See [Acceptance checks](../guides/acceptance-checks.md). |
| `--escalate [LADDER]` | off (`CERTO_MODEL_SELECTION`) | Start on the first rung of a ladder of models from `escalation.yaml`, and move to the next model only when Certo's verdict shows the model couldn't finish, or its provider fails (outage, rate limit, rejected key). The time budget (`budget_exhausted`) and `CERTO_MAX_TASK_COST` stop the climb. `LADDER` names a ladder; without it, the ladder named `default` is used, else one built from the ratings. Can't be combined with `--auto-model`, `--model` or `--resume`. A missing model file (the error says which example to copy) or an unknown ladder is a configuration error that lists the ladders found. See [Escalate between models](../guides/escalate-between-models.md). |
| `--resume` | off | Continue the last run in this folder (or in `--project NAME`) from the state in its `.certo/` folder. `TASK` is optional and is sent as an extra instruction. Errors when there is no saved state; does nothing (exit 0) when the last run ended `verified` and no `TASK` is given. See [Resume an interrupted run](../guides/resume-a-run.md). |

**Output.** A run starts with a banner: the Certo version, then one
line each for the model (with `--auto-model` or `--escalate`, how it is
chosen, or the ladder), the project folder, where the commands run
(`this computer` or Docker and its image), the checks (`on`, with
`CERTO_MAX_VERIFY_RETRIES`, or `off`) and the limits
(`CERTO_MAX_TASK_SECONDS`, `CERTO_MAX_ITERATIONS`, and
`CERTO_MAX_TASK_COST` with `--escalate`). A `Mode` line appears with
`--interactive` or `CERTO_CONFIRM_MODE=always`. For a local server, the
model line shows its host and port; the API key is never shown. A run
refused because of a wrong flag or setting prints only the error, no
banner. With `--resume`, a `Resuming:` line follows. A warning about
uncommitted changes may follow (see [Work on an existing project](../guides/work-on-an-existing-project.md)).
At the end: the agent's last message (or Certo's last note), the
`Model used:` line with `--auto-model`, then `Verification: <verdict>`,
any limitations as `-` lines, and the run summary. After a failing
verdict, a last line names `.certo/STATUS.md` and the `certo --resume`
command (unless `CERTO_SAVE_STATE` is off).

**State.** Every run keeps its state in the project's `.certo/` folder,
which git ignores. See [Resume an interrupted run](../guides/resume-a-run.md#the-certo-folder).

**Exit code.** 0 for `verified`, `inconclusive` and `unchanged`; 1 for
every other verdict, for a configuration error (`Configuration error: ...`)
and for a run-time error (`Error: ...`); 130 when you stop it with Ctrl-C.
With `--require-verification`, `inconclusive` and `unchanged` exit 1. See [Verdicts](verdicts.md).

`verify`, `init`, `check` and `bench` are subcommands only when they are
the whole first argument. `certo "verify the login flow"` runs a task. To
run the one-word task `verify`, write `certo -- verify`.

## `certo verify`

Run Certo's verification on a project, with no agent and no model.

```text
certo verify [PATH] [--require-verification]
```

| Argument or flag | Default | Effect |
|---|---|---|
| `PATH` | `.` | The project folder. |
| `--require-verification` | off | Exit 1 for `inconclusive` too. |

It needs no settings and reads no `.env`. It may create the project's
`.venv` and install pytest into it. It always runs locally, once, with no
retries. Exit code: 0 for `verified` and `inconclusive`, 1 for `failed`
and `timed_out`, and 1 if `PATH` is not a folder. See
[Verify in CI](../guides/verify-in-ci.md).

## `certo init`

Save your model settings and create a folder with sample tasks.

```text
certo init [FOLDER] [--provider {openai,anthropic,gemini,ollama,other}]
                    [--model ID] [--base-url URL] [--global | --local]
                    [--no-samples] [--no-check] [--yes] [--force]
```

| Argument or flag | Effect |
|---|---|
| `FOLDER` | The sample folder to create. Default: `./certo-workspace`. |
| `--provider {openai,anthropic,gemini,ollama,other}` | Skip the provider question. |
| `--model ID` | Skip the model question. Without `--provider`, the provider comes from the model's prefix. |
| `--base-url URL` | Skip the Ollama address question. Also sets `CERTO_LLM_BASE_URL` for any provider. |
| `--global` | Save for all projects, in the user settings file. Skip the "Save these settings for" question. |
| `--local` | Save in `FOLDER/.env` only. Skip that question. |
| `--no-samples` | With `--global`: don't create the sample folder. |
| `--no-check` | Don't make the test call to the model. |
| `--yes`, `-y` | Ask nothing and accept every default: all projects (unless `--local`), plus the sample folder. A key is used only from the provider's exported variable. |
| `--force` | Write into a folder that isn't empty, or over an existing `FOLDER/.env`. With nothing asked (`--yes`, or no terminal), also needed to replace an existing user settings file. |

**Where settings go.** "All projects on this computer" (the default) writes
the user settings file, `~/.config/certo/.env` (or
`$XDG_CONFIG_HOME/certo/.env`). "This folder only" writes `FOLDER/.env`.
Both are written with permissions `600`. The file holds your chosen lines,
then every other provider's lines commented out.

**The sample folder** gets `.gitignore` (`.env`, `projects/`,
`artifacts/`; an existing file only gains missing lines), `tasks/wordle.md`
and `tasks/asteroids.md`, and a `README.md` with next steps. A `README.md`
that `init` didn't write is never replaced. With "All projects", the
folder gets no `.env`, and a folder that already has files is skipped.

**Questions**, on a terminal: provider; model; API key (hidden), or the
Ollama address and installed model; where to save; whether to create the
sample folder. If you already have a user settings file, `init` shows its
provider and model (never the key) and asks before replacing it. Nothing
is written until the last answer, so Ctrl-C leaves everything as it was
(exit 130).

**Without a terminal** and without `--provider`, `--model` or `--yes`,
`init` asks nothing and writes `FOLDER/.env` with every provider commented
out. Without a terminal, settings go to `FOLDER/.env` unless `--global` or
`--yes` is given.

There is no `--api-key` flag, on purpose: a key on the command line is
saved in your shell history.

## `certo check`

Check that the configured model works.

```text
certo check [--timeout SECONDS] [--models]
```

| Flag | Default | Effect |
|---|---|---|
| `--timeout SECONDS` | `120` | How long to wait for each answer. A local model may need time to load. |
| `--models` | off | Also send the same test request to every model enabled in `models.yaml`, one line per model. |

It reads the settings like a run does, prints each LLM setting and where
it came from (`environment variable`, `./.env (<path>)` or
`user settings (<path>)`; the key only as `set` or `not set`), then sends
one request that offers the model a tool. It passes only if the model
answers with a tool call. Every message and its fix:
[Troubleshooting](../troubleshooting.md).

**The model files.** When `models_list.yaml` or `models.yaml` exists (see
[where Certo looks](models-yaml.md#where-certo-looks)), `certo check` also
reports them: which files it found (including the optional
`task_profiles.yaml` and `escalation.yaml`, or `none`), the active and inactive models, how
many listed models aren't used, each ladder with its usable rungs, the
ladder Certo would build from the ratings (and the models it leaves out
of it, with the model that beats each one), and every error and warning
(see [Checks](models-yaml.md#checks)). A missing file is an error with the
command that copies its example. Keys are never printed. For example:

```text
Model files:
  List: .../models_list.yaml
  Personal settings: .../models.yaml
  Task profiles: .../task_profiles.yaml
  Escalation: .../escalation.yaml
  Active models: qwen-local, gpt-luna, claude-sonnet
  Inactive models: gemma-local
  Ladder 'default': qwen-local -> gpt-luna -> claude-sonnet
  Ladder 'local-only': qwen-local (1 rung(s) skipped)
  Derived ladder: qwen-local (capability 5, cost rating 5) -> gpt-luna (capability 7, cost rating 4) -> claude-sonnet (capability 10, cost rating 2)
  Warning: Ladder 'local-only', rung 2: gemma-local has 'activated: false', so this rung is skipped.
  Warning: Ladder 'local-only' has only one usable rung (qwen-local), so it can't escalate.
```

With `--models`, each active model gets a line such as
`qwen-local (ollama/qwen3-coder:30b)... ok: reachable, tool calling works.`
A broken key or a model without tool calling shows up here, before a run.

**Exit code.** 0 when the model check passes, the catalog has no error,
and (with `--models`) every model passes; 1 otherwise. `--models` without
the model files is an error.

## `certo bench`

Compare models and strategies on tasks graded by hidden tests.

```text
certo bench [--config FILE] [--out DIR] [--resume] [--parallel N]
            [--max-cost USD] [--yes] [--list-tasks] [--check-tasks]
```

| Flag | Default | Effect |
|---|---|---|
| `--config FILE` | `bench.yaml` | The benchmark file. See [bench.yaml](bench-yaml.md). |
| `--out DIR` | `./bench-results/<date-time>` | The results folder. A folder that already has results is refused unless `--resume` is given. |
| `--resume` | off | Continue an interrupted benchmark in `--out` (default: the latest folder in `./bench-results`), skipping runs already recorded. Refused if the tasks, arms, repeats, models or task set changed. |
| `--parallel N` | `1` | Run N at a time. Refused when any arm uses a local model (Ollama, or a server on this machine or network). |
| `--max-cost USD` | none | Stop starting new runs once the recorded cost (all runs in the folder) reaches USD. Runs already started finish; results are kept. Models with no known price count as 0. |
| `--yes`, `-y` | off | Start without asking. Needed when there is no terminal. |
| `--list-tasks` | | List the tasks and exit. Needs no models. |
| `--check-tasks` | | Check every task with no model: its reference solution must pass its hidden tests, and its starter alone must fail them. Exit 1 if any task is broken. |

It reads only the benchmark file and the models file it names, never
`.env`. Before starting, it prints the plan (tasks × arms × repeats) and a
rough cost estimate: "at most" (every escalation rung runs) and, when
earlier results in the same parent folder cover the lower rungs, "likely"
(see [the cost estimate](../guides/benchmark.md#run-it)). While running, it prints one line per finished run.
At the end it writes `results.md`, `results.csv` and `cost.json`, and
prints a summary per arm and the real total cost next to the estimate. Guide: [Benchmark models and strategies](../guides/benchmark.md).

**Exit code.** 0 when the benchmark ran, whatever the models scored (also
when stopped by `--max-cost`); 1 for a configuration error, or when the
plan wasn't confirmed; 130 when interrupted (finished runs are kept).

## `certo-server`

Run Certo as an HTTP and WebSocket server. Needs the `server` extra. Its
`/v1/chat/completions` endpoint and every task store except `memory` are
[experimental](../README.md#experimental-features).

```text
certo-server [--host HOST] [--port PORT]
```

| Flag | Default | Effect |
|---|---|---|
| `--version` | | Print the version and exit. |
| `--host HOST` | `127.0.0.1` | Address to listen on. The server has no authentication. |
| `--port PORT` | `8000` | Port to listen on. |

It needs valid settings at start-up. Endpoints: [Server API](server-api.md).
Guide: [Run as a server](../guides/run-as-a-server.md).

## `certo-admin`

Maintenance: server task records, third-party skills, and a plain model
check. It reads the same settings as `certo`.

| Flag | Effect |
|---|---|
| `--version` | Print the version and exit. |

### `certo-admin show`

```text
certo-admin show TASK_ID
```

Print one task record's summary from the task store (`CERTO_TASK_STORE`).

### `certo-admin delete-task`

```text
certo-admin delete-task TASK_ID
```

Delete one task record. Exit 1 if it doesn't exist.

### `certo-admin delete-project`

```text
certo-admin delete-project PROJECT
```

Delete every task record for a project. Deleting nothing is not an error.

### `certo-admin purge`

```text
certo-admin purge [--ttl-seconds N]
```

| Flag | Default | Effect |
|---|---|---|
| `--ttl-seconds N` | `CERTO_TASK_TTL_SECONDS` | Delete finished records older than `N` seconds. |

Refuses to run (exit 1, nothing deleted) when the value is `0` or less,
because `0` means "keep forever".

### `certo-admin check-llm`

```text
certo-admin check-llm [--model MODEL] [--base-url URL] [--reasoning-effort LEVEL] [--timeout SECONDS]
```

| Flag | Default | Effect |
|---|---|---|
| `--model MODEL` | `CERTO_LLM_MODEL` | Model to check. |
| `--base-url URL` | `CERTO_LLM_BASE_URL` | Server address to check. |
| `--reasoning-effort LEVEL` | `CERTO_LLM_REASONING_EFFORT` | Reasoning effort for the check. |
| `--timeout SECONDS` | `60` | How long to wait. There are no retries. |

An older, simpler check than `certo check`: it asks for a plain text answer
and passes on any non-empty text, without testing tool calling. On failure
it prints the kind of error (`authentication`, `rate_limit`, `timeout`,
`unavailable`, `model_not_found`, `bad_request`, `setup`, `no_reply` or
`error`) and a hint. The key always comes from `CERTO_LLM_API_KEY` and is
removed from any error text. Exit 0 on success, 1 otherwise.

### `certo-admin skills`

Manage third-party skills ([experimental](../README.md#experimental-features)). Guide:
[Add skills and tools](../guides/add-skills-and-tools.md#third-party-skills).

#### `certo-admin skills install`

```text
certo-admin skills install SOURCE PATH [--ref REF]
```

| Argument or flag | Effect |
|---|---|
| `SOURCE` | `github:owner/repo`, or an `https://` git URL with no credentials in it. |
| `PATH` | The skill's folder inside the repository, e.g. `skills/pdf`. It must contain a `SKILL.md`. |
| `--ref REF` | Branch, tag or commit. Default: the repository's default branch. |

The skill is installed **disabled**. Certo prints its source, commit,
license and any warnings. A name that a first-party skill already uses is
refused.

#### `certo-admin skills list`

```text
certo-admin skills list
```

List installed skills with their state, license and commit.

#### `certo-admin skills enable`

```text
certo-admin skills enable NAME [--accept-unknown-license]
```

| Flag | Effect |
|---|---|
| `--accept-unknown-license` | Needed to enable a skill whose license is `unknown`. Read the license first. |

#### `certo-admin skills disable`

```text
certo-admin skills disable NAME
```

Stop giving the skill to the agent. The files stay.

#### `certo-admin skills update`

```text
certo-admin skills update NAME [--ref REF]
```

| Flag | Effect |
|---|---|
| `--ref REF` | Default: the ref originally requested. |

Download again. If the content or the license changed, the skill is
disabled again and an unknown-license acceptance is cleared.

#### `certo-admin skills remove`

```text
certo-admin skills remove NAME
```

Delete the skill's files and its lockfile entry.

#### `certo-admin skills sync`

```text
certo-admin skills sync
```

Restore every skill in the lockfile at its recorded commit, and check
every file against its recorded hash. A skill whose files don't match is
not installed (exit 1). Never changes which skills are enabled.
