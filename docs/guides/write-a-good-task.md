# Write a task Certo can check

This guide shows how to write a task so that the agent builds the right
thing and Certo can check it. It is for anyone who gives Certo tasks. How
Certo checks the result is in
[How verification works](../concepts/how-verification-works.md).

Certo's verdict is only as strong as the checks it can run. A task that
asks for tests, says what "done" means and fits in one run gives you a
verdict you can trust. A vague task gets a vague result, and often
`inconclusive`.

## A good task at a glance

The Wordle task that `certo init` creates is a good model. Shortened:

```markdown
# Wordle in the terminal

Build a terminal Wordle game in Python, using only the standard library.

## Rules
- The game picks a secret five-letter word. The player has six guesses.
- ...

## Files
- `wordle_logic.py`: the rules, with no input or printing. A function
  `score_guess(guess, answer)` takes two five-letter words and returns a
  list of five marks.
- `wordle.py`: the game, played with `python wordle.py`. When input ends
  (Ctrl-D) or on Ctrl-C, it says goodbye and exits without a traceback.
- `test_wordle_logic.py`: pytest tests for `score_guess` with exactly these
  cases, copied as written (they are worked out already, don't change them):
  ...

## Done when
- `python -m pytest` passes.
- `python wordle.py` starts a game.
```

The full file is `certo-workspace/tasks/wordle.md` after `certo init`. The
rules below explain why it is written this way.

## 1. Name the language and the tools

Say which language, and which libraries or frameworks are allowed: "in
Python, using only the standard library", "a Node project with Vite and
React", "a Go module".

- The agent doesn't have to guess, and you don't get a project in a
  language you didn't want.
- In an empty folder, Certo prepares a Python environment before the agent
  starts only when the task names Python.
- Certo checks a project by its type (`pyproject.toml`, `package.json`,
  `go.mod`, ...). A project of a type Certo doesn't know ends
  `inconclusive`. See
  [Verification by language](../reference/verification-by-language.md).

## 2. Ask for tests

Without tests there is nothing to prove the work right, so a Python
project with no tests ends `inconclusive`. Add "with pytest tests" (or
"with tests that `npm test` runs") to every task that builds something.

For Node, ask for tests that really exist: a `test` script that finds no
test files can still exit successfully, and then the project counts as
`verified` with nothing tested. See
[the known gap](../reference/verification-by-language.md#node-in-detail).

## 3. Give the expected answers yourself

The agent's own tests share its misunderstandings. If the agent gets a
rule wrong, it can write a test that expects the same wrong result, and
then both pass. It can also go the other way: the code is right, the test
expects the wrong thing, and the agent keeps breaking good code to satisfy
it (story 6 in [Why agents lie](../concepts/why-agents-lie.md)).

When the right answer matters, put a few worked examples in the task, as
a table of inputs and expected results, and say that the tests must use
them as written. The Wordle task does this for `score_guess`. Pick the
cases that are easy to get wrong (repeated letters, empty input, the
boundary value), not only the easy ones.

## 4. Keep the logic apart from the input and output

Certo runs every check with no input: nobody types anything. It can start
a program, but it can't play a game or choose a menu item. So ask for:

- **the logic in its own module, with no input or printing**, so tests can
  call it directly (`wordle_logic.py` above);
- **a program that exits cleanly when input ends.** Certo starts each
  Python program with standard input closed, and a program that crashes
  with an `EOFError` fails that check.

This matters most for games, menus and anything interactive. A Tower of
Hanoi game once passed every test and crashed as soon as a player chose
`SOLVE`, because the tests never went through the menu (see
[Why agents lie](../concepts/why-agents-lie.md#7-every-test-passed-and-the-game-crashed-on-solve)).

## 5. Say what "done" means

End the task with a short "Done when" list of things that can be checked:
"`python -m pytest` passes", "`npm run build` succeeds", "the README
explains how to run it".

For files that must exist or must contain something, add
[acceptance checks](acceptance-checks.md): Certo checks them itself, and a
required one that fails turns `verified` into `acceptance_failed`.

```bash
certo tasks/cli.md --project cli --acceptance-checks '[{"kind": "file_contains", "path": "README.md", "contains": "## Usage"}]'
```

You don't need to ask for a `README.md`: every agent is already told to
leave one that says how to run the project.

## 6. For a fix, make the change checkable

A task that fixes or extends an existing project is the easiest to get
wrong, because the project's tests may already pass before the agent does
anything. Then passing tests prove nothing.

- **Ask for new tests for each fix and each new feature**, so a check
  exists that fails until the work is done.
- **Name what must exist afterwards**, and check it with an acceptance
  check. For example, if the task says "define `OutOfStock` in
  `inventory.py`":

  ```json
  [{"kind": "file_contains", "path": "inventory.py", "contains": "class OutOfStock"}]
  ```

This is a real case. In Certo's first benchmark, an agent given exactly
that inventory task changed no file at all. The existing tests passed, so
Certo said `verified`. Since then, a run that changes no file ends
[`unchanged`](../reference/verdicts.md#unchanged-in-more-detail), but an
acceptance check catches a missing piece even when other files changed.

Commit your work before a task on an existing project, so you can see
exactly what the agent changed and undo it. See
[Work on an existing project](work-on-an-existing-project.md).

## 7. One step per task

A run has a time budget (30 minutes by default) and a limited number of
fix attempts. A task that asks for a whole application in one go often
runs out of both, and small local models in particular lose track of long
tasks.

Split big work into steps, each one small enough to check:

```bash
certo "Create a Python package todo with a Todo class (add, done, list) and pytest tests" --project todo
certo "Add saving and loading the list as JSON, with tests" --project todo
certo "Add a command line: todo add, todo done, todo list, with tests" --project todo
```

Each task runs in the same folder, sees the earlier work, and gets its own
verdict. Commit after each `verified` step if the folder is a git
repository.

## 8. Decide everything up front

Nobody can answer the agent during a run, so it can't ask what you meant.
Put your choices in the task: names, file layout, libraries, what to do
with bad input. If you would rather answer questions, use
[interactive mode](interactive-mode.md).

The same goes for tools that ask questions in the terminal, such as some
project scaffolders. They get no answer and may do nothing. If the task
needs one, say to run it with its non-interactive options.

## 9. Long tasks belong in a file

A task can be text in quotes, a file or a URL:

```bash
certo "Add a --verbose flag, with a test"
certo tasks/wordle.md --project wordle
certo https://example.com/tasks/wordle.md --project wordle
```

For anything longer than a sentence or two, use a Markdown file. It is
easier to write, keeps a record of what you asked, and can be reused.

## Checklist

- [ ] The language, and the libraries allowed.
- [ ] Tests asked for, and run by a standard command.
- [ ] Worked examples for the rules that are easy to get wrong.
- [ ] Logic apart from input and output; the program exits cleanly when
      input ends.
- [ ] A "Done when" list; acceptance checks for files that must exist.
- [ ] For a fix: new tests, and what must exist afterwards.
- [ ] Small enough for one run.
- [ ] No open questions.

## Related

- [What to do after each verdict](after-the-verdict.md)
- [Acceptance checks](acceptance-checks.md)
- [Verification by language](../reference/verification-by-language.md)
- [Why agents lie](../concepts/why-agents-lie.md)
