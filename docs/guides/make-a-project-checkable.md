# Make your project checkable

This guide shows how to set up a project so Certo can check it and say
`verified` instead of `inconclusive`. It is for anyone who runs Certo on
their own projects, or uses `certo verify` in CI. The exact rules per
language are in
[Verification by language](../reference/verification-by-language.md).

Certo never invents a check. It runs only what the project itself sets
up: its tests, its build, its configured lint tools. So a project is as
checkable as its own setup.

## Try it first

`certo verify` runs the same checks as an agent run, with no agent and no
model. It costs nothing, so use it to see where a project stands:

```bash
certo verify            # the current folder
certo verify my-project
```

Each line shows a check and its status (`passed`, `failed`, `skipped`,
`unavailable`, `timed_out`), and the last line is the verdict. The steps
below fix the usual reasons for `inconclusive`.

## 1. One project at the top of the folder

Certo decides the project type from one file at the top of the folder:
`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`, `pom.xml` or a
Gradle build file.

- **No such file:** the type is unknown and nothing runs. A folder with
  only `.py` files still counts as Python.
- **Several projects side by side** (`frontend/package.json` and
  `backend/pyproject.toml`, nothing at the top): Certo can't choose, and
  the verdict is `inconclusive`. Run Certo, or `certo verify`, in each
  sub-project folder, for example as two CI steps.

## 2. Tests that really run

The main check decides `verified`. It is the project's test command, or
for Node its build. A project with no tests can't be `verified`, because
nothing proves it works.

Make sure the tests:

- **are found** by the standard command, with no extra arguments;
- **fail when the code is wrong.** A test that only checks that the code
  runs proves little;
- **finish within 5 minutes.** Every check has a 300-second limit;
- **need no input and no network**, and don't wait for anything. Certo
  runs every check with standard input closed. A test that starts a server
  must stop it.

## 3. Your language

### Python

- **Tests:** `test_*.py` or `*_test.py` files that `pytest` finds from the
  project folder. If the project has tests but pytest isn't installed,
  Certo installs it into the project's environment.
- **Dependencies:** Certo runs everything in the project's own
  environment, never its own. With a `uv.lock`, it runs through `uv run`,
  which installs the locked dependencies. With a `.venv` or `venv`, it uses
  that one as it is, so install the project's dependencies into it first.
  Without either, Certo creates a new `.venv` and installs only pytest:
  tests that import other packages then fail. Use `uv lock`, or create the
  `.venv` with the dependencies yourself, before `certo verify`.
- **Lint and types:** `ruff check .` runs when ruff is configured (a
  `[tool.ruff]` section in `pyproject.toml`, or a `ruff.toml`) and installed
  in the project environment. The same for mypy (`[tool.mypy]` or
  `mypy.ini`). Certo doesn't install either. They can only turn a pass into
  a failure.
- **Programs:** for every file with an `if __name__ == "__main__":` block,
  Certo checks that the block is the last thing in the file, and runs the
  file with no input. So put the block at the end, and make the program
  exit cleanly when input ends instead of crashing with an `EOFError`.
  Keep the logic in functions that tests can import, apart from the code
  that reads input.

### Node, JavaScript and TypeScript

- **Main check:** `npm run build` when `package.json` has a `build`
  script, otherwise `npm test`. With neither, the verdict is
  `inconclusive`. npm's placeholder `test` script (`echo "Error: no test
  specified" && exit 1`) doesn't count.
- **Tests:** when there is a `build` script, `npm test` still runs as an
  extra check, if the project has a real `test` script. Both run with
  `CI=true`, so test runners don't start in watch mode.
- **Make sure the tests exist.** Certo goes by the exit code, and some
  runners, including `node --test`, succeed when they find no test files.
  Then the project counts as `verified` with nothing tested. Run `npm test`
  yourself once and check that it reports some tests.
- **Lint and types:** `npm run lint` and `npm run typecheck` (or
  `type-check`) run when those scripts exist. For TypeScript, a
  `"typecheck": "tsc --noEmit"` script makes Certo check the types. Certo
  doesn't read ESLint or `tsconfig.json` settings by itself.
- **Dependencies:** Certo doesn't install Node packages. Run `npm ci` (or
  `npm install`) before `certo verify`, for example as a CI step before it.
  Commit `package-lock.json` so CI installs the same versions.

### Go

`go test ./...` is the main check, and `go vet ./...` runs too. Put
`go.mod` at the top of the folder and keep tests in `_test.go` files.
`go` must be installed.

### Rust

`cargo test` is the main check; `cargo check` and `cargo clippy` run too.
Install clippy with `rustup component add clippy`: without it the project
fails today, instead of being reported as missing a tool (a known bug).

### Java

`mvn test` for Maven, `gradle test` for Gradle. **Commit the wrapper**
(`./mvnw` or `./gradlew`): Certo uses it when it exists, so the project
can be checked on a machine that has Java but no Maven or Gradle. Without
the wrapper or the tool, the verdict is `inconclusive`.

### Other languages

Ruby, PHP, .NET, C and C++ are not covered yet: their projects are
`inconclusive`. A standalone HTML page isn't run either; add a
`package.json` with a `test` or `build` script to make it checkable.

## 4. The tools on the machine

Certo runs the project's own tools and never installs a toolchain. The
machine that runs the check, your laptop or the CI runner, needs the
language's tools: Python 3, Node with npm, Go, Rust with cargo, or Java.
A missing tool makes its check `unavailable`, and the verdict
`inconclusive`. See
[What CI needs installed](verify-in-ci.md#what-ci-needs-installed).

## 5. Let the agent keep it that way

When Certo's agent works on the project, put the same rules in the task
("with pytest tests", "keep `npm test` running the tests"), or once for
the whole project in an `AGENTS.md`. See
[Write a task Certo can check](write-a-good-task.md) and
[Work on an existing project](work-on-an-existing-project.md#tell-the-agent-about-the-project-agentsmd).

## Checklist

- [ ] One project file at the top of the folder.
- [ ] Tests that the standard command finds, that can fail, and that need
      no input, no network and under 5 minutes.
- [ ] Python: dependencies in a `uv.lock` or an installed `.venv`; the
      `__main__` block last; a clean exit when input ends.
- [ ] Node: a `build` or a real `test` script that runs real tests;
      `npm ci` before checking; the lockfile committed.
- [ ] Rust: clippy installed. Java: the wrapper committed.
- [ ] The language's tools installed where the check runs.
- [ ] `certo verify` says `verified`.

## Related

- [Verification by language](../reference/verification-by-language.md):
  every check, exactly.
- [Verify in CI](verify-in-ci.md)
- [Verdicts](../reference/verdicts.md)
- [Troubleshooting: verdicts](../troubleshooting.md#verdicts)
