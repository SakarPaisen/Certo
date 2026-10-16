# Configuration

Every setting Certo reads: its default, what it does, and where Certo looks
for it. It is for looking things up. To set up a model the easy way, see
[Getting started](../getting-started.md).

## Where Certo looks

All settings are environment variables. Certo looks for each one in three
places, in this order, and uses the first value it finds:

| Order | Place | Written by |
|---|---|---|
| 1 | A variable exported in your shell | you |
| 2 | `.env` in the folder where you run `certo` | you, or `certo init --local` |
| 3 | The user settings file: `$XDG_CONFIG_HOME/certo/.env`, or `~/.config/certo/.env` when `XDG_CONFIG_HOME` is not set or not an absolute path. The same path on macOS, Linux and Windows. | `certo init` (the default, `--global`) |

- Each setting is looked up on its own. A project's `.env` can set only
  `CERTO_LLM_MODEL` and still get `CERTO_LLM_API_KEY` from the user file.
- An empty value (`CERTO_LLM_API_KEY=`) counts as not set, so it doesn't
  hide a value from a later place.
- `${VAR}` inside either file is replaced with the value of `VAR`.
- `certo check` shows where each LLM setting came from.
- `certo verify` reads no settings at all.

Relative paths, such as `./projects`, are relative to the folder where you
run `certo`.

**Value formats.** Yes/no settings accept `1`, `true`, `yes`, `on` and
`0`, `false`, `no`, `off` (any case). Choice settings ignore case. Number
settings must be whole numbers; an invalid value stops Certo with a
`Configuration error` that names the variable.

**Old names.** Before the rename to Certo, settings were called
`HARNESS_*`. An old `HARNESS_` name is still read when the `CERTO_` one is
not set, with a warning to rename it. This does not apply to the LLM
settings: the bare `LLM_MODEL`, `LLM_API_KEY`, `LLM_BASE_URL` and
`LLM_REASONING_EFFORT` (used up to version 0.1.1) are never read, so other
tools' variables can't leak in. If one is set while the `CERTO_LLM_` one is
missing, the error message names it.

## Model

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_LLM_MODEL` | **required** | The model, as a [LiteLLM model id](https://docs.litellm.ai/docs/providers): `provider/model`, e.g. `anthropic/claude-sonnet-5-5`, `openai/gpt-6.1-sol`, `ollama/qwen3-coder:30b`. Changing this is the only thing needed to switch provider. |
| `CERTO_LLM_API_KEY` | required, unless `CERTO_LLM_BASE_URL` is set | The key for the provider in `CERTO_LLM_MODEL`. |
| `CERTO_LLM_BASE_URL` | empty | The server address, for a local or self-hosted model, e.g. `http://localhost:11434`. In a `.env` file, leave the line with nothing after `=` when unused: `python-dotenv` keeps a trailing `# comment` on an otherwise empty value as the value itself. |
| `CERTO_LLM_REASONING_EFFORT` | empty | How much the model should think: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, or any value your provider accepts (not checked by Certo). `none` or `off` sends no reasoning setting. Empty means `high`, except for `ollama/` and `ollama_chat/` models, where empty means none. |
| `CERTO_LLM_TIMEOUT_SECONDS` | `300` | How long one call to the model may take, in seconds. A call that takes longer fails and is tried again from the start, up to 5 more times. `0` means no limit. Raise it for slow local models; see [Ollama and local models](../guides/ollama-and-local-models.md#make-sure-the-model-fits-in-memory). |

Per-run overrides: `--model`, `--api-key`, `--base-url`,
`--reasoning-effort` (see [Commands](commands.md#certo)).

## Where the agent works

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_WORKSPACE` | `.` | The folder the agent works in when `--project` is not given. |
| `CERTO_PROJECTS_DIR` | `./projects` | The parent folder for `--project NAME`, which becomes `CERTO_PROJECTS_DIR/NAME`. |
| `CERTO_NO_WORKTREE_WARNING` | `false` | `true` turns off the warning printed before the agent edits a folder with uncommitted changes, or a folder outside git. |
| `CERTO_SAVE_STATE` | `true` | The `certo` command keeps the last run's state in the project's `.certo/` folder, for `certo --resume`. `false` turns this off (`--resume` still saves). Server mode and `certo bench` never write it. See [Resume an interrupted run](../guides/resume-a-run.md). |

## Limits and verification

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_MAX_ITERATIONS` | `50` | The most steps the agent may take in one run. Each retry after a failed check is a new run with the same limit. |
| `CERTO_MAX_TASK_SECONDS` | `1800` | The time budget for the whole task, in seconds: the first run plus every retry. When it runs out, the verdict is `budget_exhausted`. Checked between runs, so a single slow step can go a little past it. |
| `CERTO_VERIFY_TESTS` | `always` | `always` or `never`. With `never`, Certo doesn't check the result, and the verdict is always `inconclusive`. |
| `CERTO_MAX_VERIFY_RETRIES` | `2` | How many times a failure is sent back to the agent to fix. Must be at least 1. Also used for unfinished to-do items. |
| `CERTO_CONFIRM_MODE` | `never` | `never` or `always`. `always` asks you to approve every action. See [Interactive and confirm mode](../guides/interactive-mode.md). |
| `CERTO_INTERACTIVE` | `false` | Let the agent stop and ask you questions. The same as `--interactive`. Has no useful effect in server mode. |

## Execution

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_EXECUTION` | `local` | `local` or `docker`: where the agent's tools run. See [Run in Docker](../guides/run-in-docker.md). |
| `CERTO_DOCKER_IMAGE` | `certo/agent-server:local` | The image for Docker mode. Built on first use from a source checkout. |
| `CERTO_DOCKER_PLATFORM` | `linux/arm64` on ARM machines, `linux/amd64` otherwise | `linux/amd64` or `linux/arm64`. Leave empty to detect. |

## Automatic model selection

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_MODEL_SELECTION` | `manual` | `manual`, `auto` or `escalate`. `auto` is the same as `--auto-model`, `escalate` the same as `--escalate`. |
| `CERTO_MODELS_FILE` | `./models.yaml` | The model list. Read when selection is `auto` or `escalate`, and by `certo check`. See [models.yaml](models-yaml.md). |
| `CERTO_MAX_TASK_COST` | empty | A cap, in US dollars, on an escalation run. Before each rung starts, Certo stops climbing if the cost recorded so far has reached it, and keeps the verdict it has. Models with no known price count as 0, and the note says so. Empty means no cap. Used only by escalation. |
| `CERTO_ESCALATION_LADDER` | empty | With `escalate`: the ladder in `models.yaml` to climb. Empty uses the ladder named `default`, or one built from the ratings. |

## Skills

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_SKILLS_DIR` | `./skills` | Your own skills, loaded on top of the built-in ones. A missing folder is fine. |
| `CERTO_THIRD_PARTY_SKILLS_DIR` | `./third_party_skills` | Where `certo-admin skills` installs third-party skills. Must not be inside, or contain, `CERTO_SKILLS_DIR` or the built-in skills folder. |
| `CERTO_THIRD_PARTY_SKILLS_LOCK` | `./third_party_skills.lock.json` | The lockfile for third-party skills: source, commit, license, hashes and enabled state. Never the skill content. |

## Run records

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_ARTIFACTS_DIR` | empty (off) | A folder where each run writes `metadata.json`, `transcript.json` and `metrics.json`. See [Run records and costs](../guides/run-records-and-costs.md). |

## Server task records

Read only by `certo-server` and `certo-admin`. See
[Run as a server](../guides/run-as-a-server.md#keep-task-records).

| Variable | Default | Meaning |
|---|---|---|
| `CERTO_TASK_STORE` | `memory` | `memory`, `sqlite`, `mysql`, `postgres` or `redis`. |
| `CERTO_TASK_TTL_SECONDS` | `0` | Seconds to keep a finished task record. `0` keeps records forever. |
| `CERTO_TASK_STORE_SQLITE_PATH` | `./certo_tasks.db` | sqlite: the database file. |
| `CERTO_TASK_STORE_MYSQL_HOST` | `localhost` | mysql: host. |
| `CERTO_TASK_STORE_MYSQL_PORT` | `3306` | mysql: port. |
| `CERTO_TASK_STORE_MYSQL_USER` | `root` | mysql: user. |
| `CERTO_TASK_STORE_MYSQL_PASSWORD` | empty | mysql: password. |
| `CERTO_TASK_STORE_MYSQL_DATABASE` | `certo` | mysql: database. |
| `CERTO_TASK_STORE_POSTGRES_HOST` | `localhost` | postgres: host. |
| `CERTO_TASK_STORE_POSTGRES_PORT` | `5432` | postgres: port. |
| `CERTO_TASK_STORE_POSTGRES_USER` | `postgres` | postgres: user. |
| `CERTO_TASK_STORE_POSTGRES_PASSWORD` | empty | postgres: password. |
| `CERTO_TASK_STORE_POSTGRES_DATABASE` | `certo` | postgres: database. |
| `CERTO_TASK_STORE_REDIS_HOST` | `localhost` | redis: host. |
| `CERTO_TASK_STORE_REDIS_PORT` | `6379` | redis: port. |
| `CERTO_TASK_STORE_REDIS_DB` | `0` | redis: database number. |
| `CERTO_TASK_STORE_REDIS_PASSWORD` | empty | redis: password. |
| `CERTO_TASK_STORE_REDIS_USE_TLS` | `false` | redis: connect with TLS. |

**Stores created before the rename to Certo** keep working:

- sqlite: if the path is left at its default, `./certo_tasks.db` doesn't
  exist and `./harness_tasks.db` does, the old file is used, with a
  warning.
- SQL table: an old `harness_tasks` table is used (with a warning) when
  there is no `certo_tasks` table. Rename it when convenient:
  `ALTER TABLE harness_tasks RENAME TO certo_tasks`.
- mysql/postgres database: the default name changed from `harness` to
  `certo`, with no automatic fallback. To keep an old database, set
  `CERTO_TASK_STORE_MYSQL_DATABASE=harness` (or the `POSTGRES` one).
- redis: keys moved from `harness:` to `certo:`. Old keys are still read
  and move to the new name when a record is saved.

## Other variables Certo uses

| Variable | Meaning |
|---|---|
| `XDG_CONFIG_HOME` | Changes where the user settings file is (see the table at the top). |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` | Read only by `certo init`, which offers to reuse them (and then writes `CERTO_LLM_API_KEY=${...}`). |
| `OPENHANDS_SUPPRESS_BANNER` | Certo sets it to `1` unless you set it, to hide the OpenHands start-up banner. |
| `LITELLM_MODE` | Certo sets it to `PRODUCTION` unless you set it. Otherwise LiteLLM loads a `.env` file of its own, found from its install folder, which could override your settings. |
