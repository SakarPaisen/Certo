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
