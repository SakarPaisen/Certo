"""Shared test helpers."""

from __future__ import annotations

import glob
import os
import subprocess
import sys
import sysconfig
import tempfile

import pytest

# Certo reads a user settings file from $XDG_CONFIG_HOME/certo/.env. Point
# it at an empty temporary folder before any test module is imported (some
# call load_config() at collection time), so no test reads or writes the
# real ~/.config. Tests that need the file set their own folder.
os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="certo-tests-xdg-")
# Likewise, never read a real models.yaml (it holds keys, and `certo check`
# reports it): tests that need a catalog write their own.
os.environ["CERTO_MODELS_FILE"] = os.path.join(
    tempfile.mkdtemp(prefix="certo-tests-models-"), "models.yaml"
)


def make_project_venv(project_dir) -> str:
    """Give `project_dir` a `.venv` that can already import pytest and ruff,
    without the network: a pip-less venv from the test interpreter, with a
    `.pth` pointing at the test environment's site-packages.

    Verification then finds and reuses this environment instead of creating
    one and installing pytest from the index. Test-only: the product never
    links a project environment to its own.
    """
    venv = os.path.join(str(project_dir), ".venv")
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", venv], check=True)
    site = glob.glob(os.path.join(venv, "lib", "python*", "site-packages"))[0]
    with open(os.path.join(site, "certo_tests.pth"), "w", encoding="utf-8") as f:
        f.write(sysconfig.get_path("purelib") + "\n")
    return venv


@pytest.fixture
def project_venv():
    return make_project_venv


@pytest.fixture(autouse=True)
def _restore_environ():
    """Undo whatever a test leaves in os.environ. load_config() copies .env
    and user-file values into it, which monkeypatch doesn't track."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)
