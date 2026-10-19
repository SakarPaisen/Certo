# Examples

Task files to try Certo on, and a script that runs one task with several
models so you can compare them.

## Task files

Each file is a task description you can give to Certo as it is:

| File | What it asks for |
|---|---|
| `asteroids.md` | An asteroid-dodging arcade game for the browser, in JavaScript |
| `hanoi.md` | A Tower of Hanoi game in the terminal, in Python |
| `invaders.md` | A Space Invaders–style game for the browser, in JavaScript |
| `mazeman.md` | A maze-chase arcade game for the browser |

The browser games need Node 18 or newer.

```bash
certo examples/hanoi.md --project hanoi
```

## Compare models on the same task

`compare-models.sh.example` runs one task with every model in a list, one
after the other. Each model builds its own copy of the project, and the
script ends with a table of verdicts, times and costs. In short:

```bash
cp examples/compare-models.sh.example compare-models.sh
chmod +x compare-models.sh
# edit the model lines between the two "# ----" markers, then:
export ANTHROPIC_API_KEY=...   # one variable per provider you listed
./compare-models.sh examples/hanoi.md
```

How to write the model lines, where the results go and how to read
them: [Compare models on one task](../docs/guides/compare-models-on-a-task.md).
