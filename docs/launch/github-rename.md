# Launch notes: GitHub and PyPI for the Certo rename

Prepared, **not applied**. Everything in the repository is already renamed
to Certo. These are the steps that need the GitHub repo or PyPI account,
so they're done by hand.

## 1. Rename the GitHub repository

`alessioricco/ARICode` → `alessioricco/certo`

- GitHub → repo **Settings → General → Repository name** → `certo`.
- GitHub redirects the old URL (web, `git clone`, `git fetch`/`push`)
  to the new one, so existing clones keep working. The docs already link
  to `https://github.com/alessioricco/certo`.
- The redirect breaks if a new repo named `ARICode` is ever created
  under the same account. Don't reuse the old name.
- Then point the local clone at the new URL, to stop relying on the
  redirect:

  ```bash
  git remote set-url origin https://github.com/alessioricco/certo.git
  ```

## 2. Repository description (the line under the repo name)

> Certo — a model-agnostic coding agent on the OpenHands SDK that
> re-runs your project's own tests before it calls a task done.

## 3. Topics

Replace any ARICode-specific topics with:

```
coding-agent  ai-agents  llm  openhands  openhands-sdk  litellm
model-agnostic  autonomous-agents  software-engineering  developer-tools
python
```

(The current topics couldn't be read from here because the `gh` CLI isn't
installed. Remove any topic that names `aricode`.)

## 4. PyPI (only if/when publishing)

- Distribution name in `pyproject.toml`: `certo`.
- On 2026-10-14 `https://pypi.org/pypi/certo/json` returned 404, so the
  name looks unclaimed. PyPI can still refuse a name that's too similar
  to an existing project, and the only real check is the first upload.
  Nothing has been published.
- Console scripts installed by the package: `certo`, `certo-server`,
  `certo-admin`, plus the aliases `harness`, `harness-server` and
  `harness-admin`. A bare `harness` command on PyPI users' PATH could
  collide with other tools. Consider dropping the aliases before a first
  public release, since nobody outside this repo depends on them yet.

## 5. Not needed

- No Docker registry push. The image tag `certo/agent-server:local` is
  built locally on first use.
- No tags or releases to rename.
