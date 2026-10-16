# Verdicts

Every verdict (verification state) Certo can report, what it means, and
its exit code. It is for looking things up and for scripts. Why Certo works
this way is in [How verification works](../concepts/how-verification-works.md).

## Where you see the verdict

- **`certo`** prints `Verification: <verdict>` near the end, followed by
  any limitations as `-` lines.
- **`certo verify`** prints the same line.
- **Server mode** returns it as `verification_state` in
  `GET /tasks/{task_id}` and in the WebSocket `result` message. See
  [Server API](server-api.md).

## All verdicts

| Verdict | Meaning | Exit code |
|---|---|---|
| `verified` | The project's main check (its tests, or its build) ran and passed, and no other check failed. | 0 |
| `inconclusive` | Nothing could prove the work is right, and nothing proved it wrong. See below. | 0 (1 with `--require-verification`) |
| `failed` | A check ran and failed. Only `certo verify` ends with this verdict; an agent run sends the failure back to the agent instead. | 1 |
| `retry_exhausted` | A check kept failing after `CERTO_MAX_VERIFY_RETRIES` fix attempts (2 by default), and the failure changed between attempts. | 1 |
| `no_progress` | A fix attempt changed nothing: the same check failed again with the same exit code and the same output (only timings may differ). Certo stops early instead of using up the retries. | 1 |
| `timed_out` | A check ran longer than 300 seconds and was stopped, and it still did after the fix attempts. Usually a program that hangs or waits for input. | 1 |
| `incomplete` | The agent's own to-do list still had open items after Certo asked it to finish them. Certo doesn't run the project's checks in this case. | 1 |
| `confirmation_required` | Confirm mode (`CERTO_CONFIRM_MODE=always`) needed an approval and nobody could give it (server mode). The action was rejected and the task stopped. | 1 |
| `budget_exhausted` | The task's time budget (`CERTO_MAX_TASK_SECONDS`, 30 minutes by default) ran out. | 1 |
| `acceptance_failed` | Everything else passed, but a required [acceptance check](../guides/acceptance-checks.md) failed. | 1 |
| `stuck` | The agent's run ended in a stuck or error state instead of finishing. Certo doesn't verify a run that never finished properly. | 1 |

The run itself can also fail before any verdict, for example with a
configuration error or a provider error. Then Certo prints
`Configuration error: ...` or `Error: ...` and exits 1.

## `inconclusive` in more detail

`inconclusive` is not a failure: nothing was shown to be broken. It is not
a pass either. It happens when:

- **The project has no tests yet.** For Python, no test files, or pytest
  found zero tests. This case is silent: no extra note.
- **The project type is unknown.** No `pyproject.toml`, `package.json`,
  `go.mod`, `Cargo.toml`, `pom.xml` or Gradle file, and no `.py` files.
  The note lists the files Certo found. A standalone HTML page lands here.
- **A required tool is missing**, such as `npm`, `go`, `cargo`, `mvn` or
  `gradle`, or pytest couldn't be installed.
- **The folder holds several projects** with no single one at the top. The
  note names them.
- **Verification is turned off** (`CERTO_VERIFY_TESTS=never`).

Use `--require-verification` (or `"require_verification": true` in server
mode) to treat `inconclusive` as a failure.

## The order of the checks

Certo checks, in this order, and stops at the first that applies:

1. Before and during every agent run (the first one and each retry): is
   the time budget used up? → `budget_exhausted`. Did confirm mode need an
   answer nobody could give? → `confirmation_required`
2. After a run: did it end stuck or in error? → `stuck`
3. Does the agent's to-do list have open items? Ask the agent to finish
   them; if they stay open → `incomplete`
4. Run the project's checks. On a failure, send it to the agent and check
   again → `verified`, `inconclusive`, `retry_exhausted`, `no_progress` or
   `timed_out`
5. Run the acceptance checks, if any → may turn `verified` into
   `acceptance_failed`

## Check statuses

Each single check (one command) also has a status. `certo verify` prints
it at the start of each line:

| Status | Meaning |
|---|---|
| `passed` | The command ran and succeeded. |
| `failed` | The command ran and failed. |
| `skipped` | Nothing to check here, e.g. no tests yet. Not a problem. |
| `unavailable` | It should be checkable but isn't, e.g. the tool isn't installed. Listed as a limitation. |
| `timed_out` | The command ran longer than 300 seconds and was stopped. |

How check statuses combine into a verdict is in
[How verification works](../concepts/how-verification-works.md).
