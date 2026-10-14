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

## Releasing

Releases are published to PyPI by `.github/workflows/release.yml` through
trusted publishing. There is no API token to manage.

1. Bump `version` in `pyproject.toml` (for example `0.1.0` → `0.1.1`).
2. Commit it: `git commit -am "Release vX.Y.Z"`.
3. Tag and push: `git tag vX.Y.Z && git push && git push --tags`.
4. The workflow checks that the tag matches the version in
   `pyproject.toml`, runs the full test suite, builds the sdist and wheel,
   runs `twine check`, and publishes. A mismatch or a failing test stops it
   before anything is built.

**A version number can never be reused.** PyPI rejects a re-upload of any
version that was ever published, even if it was deleted. If a release
comes out broken, fix it and release the next version.
