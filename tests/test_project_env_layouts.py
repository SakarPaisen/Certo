"""Runner paths follow the project environment, including Windows layouts."""

import os

import pytest
from test_project_env import FakeRunner, _FakeWorkspace, _result

from certo.project_env import (
    LocalRunner,
    WorkspaceRunner,
    ensure_project_env,
    install_into_env,
)


@pytest.mark.parametrize("name", [".venv", "venv"])
@pytest.mark.parametrize(
    "scripts, executable, separator, base_path",
    [
        ("bin", "python", ":", "/usr/bin:/bin"),
        ("Scripts", "python.exe", ";", r"C:\Windows\System32;C:\tools"),
    ],
)
def test_existing_environment_uses_its_own_layout(
    tmp_path, name, scripts, executable, separator, base_path
):
    venv = tmp_path / name
    (venv / scripts).mkdir(parents=True)
    (venv / scripts / executable).touch()
    runner = FakeRunner(path=base_path)

    setup = ensure_project_env(str(tmp_path), runner)

    python = f"{venv}/{scripts}/{executable}"
    assert setup.env.python == (python,)
    assert setup.env.env_vars(base_path) == {
        "VIRTUAL_ENV": str(venv),
        "PATH": f"{venv}/{scripts}{separator}{base_path}",
    }
    assert runner.commands == [[python, "-c", "import sys"]]


@pytest.mark.parametrize("uv", [None, "/tools/uv"])
@pytest.mark.parametrize("has_pip", [False, True])
def test_windows_dependency_install_uses_the_project_interpreter(tmp_path, uv, has_pip):
    scripts = tmp_path / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / "python.exe").touch()
    if has_pip:
        (scripts / "pip.exe").touch()
    runner = FakeRunner(tools={"uv": uv} if uv else {})
    env = ensure_project_env(str(tmp_path), runner).env

    result = install_into_env(env, runner, "pytest", str(tmp_path))

    python = f"{scripts.parent}/Scripts/python.exe"
    assert result.returncode == 0
    if uv:
        assert runner.commands[-1] == [
            uv,
            "pip",
            "install",
            "--quiet",
            "--python",
            python,
            "pytest",
        ]
    else:
        assert runner.commands[-1] == [python, "-m", "pip", "install", "--quiet", "pytest"]
    expected_hint = (
        "python -m pip install <package>" if has_pip or not uv else "uv pip install <package>"
    )
    assert env.install_hint == expected_hint


def test_uv_project_uses_native_scripts_before_the_environment_exists(tmp_path, monkeypatch):
    (tmp_path / "uv.lock").touch()
    monkeypatch.setattr(
        LocalRunner, "which", lambda self, name: "/tools/uv" if name == "uv" else None
    )

    env = ensure_project_env(str(tmp_path)).env
    scripts = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    runner = FakeRunner()
    install_into_env(env, runner, "pytest", str(tmp_path))

    assert runner.commands[-1][0] == f"{tmp_path / '.venv'}/{scripts}/{executable}"


def test_docker_environment_keeps_linux_paths_with_windows_files_on_the_host(tmp_path):
    scripts = tmp_path / ".venv" / "Scripts"
    scripts.mkdir(parents=True)
    (scripts / "python.exe").touch()
    workspace = _FakeWorkspace(_result(stdout="/tools/uv\n"))
    runner = WorkspaceRunner(workspace, str(tmp_path), "/workspace")

    env = ensure_project_env(str(tmp_path), runner).env

    assert env.python == ("/workspace/.venv/bin/python",)
    assert env.env_vars("/usr/bin:/bin") == {
        "VIRTUAL_ENV": "/workspace/.venv",
        "PATH": "/workspace/.venv/bin:/usr/bin:/bin",
    }
