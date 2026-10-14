"""The version is written in three places; a bump must update all of them.

Versioning rule (see CLAUDE.md): every added feature bumps the third digit.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

from certo import __version__, admin_cli, cli, server

_ROOT = Path(__file__).resolve().parent.parent


def _pyproject_version() -> str:
    with open(_ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)["project"]["version"]


def _uv_lock_version() -> str:
    with open(_ROOT / "uv.lock", "rb") as f:
        packages = tomllib.load(f)["package"]
    return next(p["version"] for p in packages if p["name"] == "certo")


def test_package_version_matches_pyproject():
    assert __version__ == _pyproject_version()


def test_uv_lock_matches_pyproject():
    # Release CI installs with `uv sync --locked`, which fails on a stale lock:
    # run `uv lock` after bumping.
    assert _uv_lock_version() == _pyproject_version()


@pytest.mark.parametrize(
    ("main", "prog"),
    [(cli.main, "certo"), (admin_cli.main, "certo-admin"), (server.main, "certo-server")],
)
def test_version_flag(main, prog, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"{prog} {__version__}"
