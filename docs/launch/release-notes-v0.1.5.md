# Certo v0.1.5

Use Certo in any folder, with your settings saved once for the whole
computer.

## New

- **A settings file for all your projects.** Certo now also reads
  `~/.config/certo/.env` (or `$XDG_CONFIG_HOME/certo/.env`), on every
  platform. Each setting is looked up on its own, in this order:
  1. a variable exported in your shell;
  2. `.env` in the current folder;
  3. the user settings file.

  So a project's `.env` can change only `CERTO_LLM_MODEL` and still use
  the key from the user file, without a copy of your key in every
  project. A blank line such as `CERTO_LLM_API_KEY=` counts as unset and
  doesn't hide a later source. When no model is set anywhere, the error
  lists the three places Certo looked.
- **`certo init` asks where to save the settings**, after the model
  questions:

  ```
  Save these settings for:
    1. All projects on this computer (recommended)
    2. This folder only
  Choice [1]:
  ```

  - For all projects, it writes the user file (permissions `600`). If one
    already exists, it shows its provider and model, never the key, and
    asks before replacing it. Then it offers the folder with the sample
    tasks, now without a `.env` inside.
  - "This folder only" is the 0.1.4 behaviour.
  - `--global` and `--local` skip the question, `--no-samples` skips the
    sample folder, and `--yes` picks all projects. Without a terminal and
    without flags, nothing changes from 0.1.4.
  - With `--yes` or no terminal, an existing user file is replaced only
    with `--force`.
- **One project at a time.** With the settings saved for all projects:

  ```bash
  cd any-project && certo "Add a --verbose flag, with a test"
  ```
- **`certo check` shows where each setting comes from**: an environment
  variable, `./.env` or the user file, with its path. The key is shown
  only as `set` or `not set`. It works from any folder.
- **A warning before the agent edits an existing folder.** Before a task
  starts in a folder that has files, Certo prints one line:
  - in a git repository with uncommitted changes, a warning to commit or
    stash first if you want to be able to roll back;
  - outside git, a note that the changes can't be rolled back with git.

  It never asks and never stops the task. Empty folders and `--project`
  folders Certo created get nothing. `CERTO_NO_WORKTREE_WARNING=1`
  turns it off.

## Upgrading

```bash
uv tool upgrade certo      # or: pip install -U certo
certo init --global        # optional: save your settings for all projects
```

An existing workspace keeps working unchanged: its `.env` is still read,
and it wins over the user file.
