# Contributing

Issues and pull requests are welcome. To work on the code:

```bash
git clone https://github.com/alessioricco/certo.git
cd certo
uv pip install -e ".[dev]"
uv run pytest -q     # no API key needed
```

See [`CLAUDE.md`](CLAUDE.md) for the project's working rules and
[`MANUAL.md`](MANUAL.md) for how the harness behaves.

## Versioning

Each change that adds a feature bumps the third digit of the version
(`0.1.2` → `0.1.3`) in the same commit. The first two digits change only for
a deliberate bigger release. Update `version` in `pyproject.toml` and
`__version__` in `src/certo/__init__.py`, then run `uv lock`;
`tests/test_version.py` fails if the three disagree. `certo --version`
shows the installed version.

## Releasing

Releases are published to PyPI by `.github/workflows/release.yml` through
trusted publishing. There is no API token to manage.

1. Make sure the version in `pyproject.toml` is one PyPI has never seen.
   Features already bumped it (see Versioning); bump the third digit if
   only fixes went in since the last release. Run `scripts/release_check.sh`
   (add `--with-llm` with a model exported): it installs the wheel the way
   users do and checks it outside the dev venv.
2. Commit any change: `git commit -am "Release vX.Y.Z"`.
3. Tag and push: `git tag vX.Y.Z && git push && git push --tags`.
4. The workflow checks that the tag matches the version in
   `pyproject.toml`, runs the full test suite, builds the sdist and wheel,
   runs `twine check` and `scripts/release_check.sh` on that wheel, and
   publishes. A mismatch or a failing test stops it
   before anything is built.

**A version number can never be reused.** PyPI rejects a re-upload of any
version that was ever published, even if it was deleted. If a release
comes out broken, fix it and release the next version.
