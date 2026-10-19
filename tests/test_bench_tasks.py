"""The bundled benchmark tasks are valid: each reference solution passes its
hidden tests and the starter alone fails them. No model involved."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from certo import bench_tasks
from certo.bench_tasks import (
    BUILTIN_TASKS_DIR,
    BenchTaskError,
    grade,
    load_tasks,
    prepare_workspace,
)

TASKS = load_tasks()


def _workspace(tmp_path: Path, task, make_venv, *, solved: bool) -> Path:
    workspace = tmp_path / "ws"
    prepare_workspace(task, workspace, solved=solved)
    if task.language == "python":
        # Offline: a venv that already sees the test environment's pytest.
        make_venv(workspace)
    elif shutil.which("node") is None:
        pytest.skip("node is not installed")
    return workspace


def test_bundled_task_set_shape():
    assert TASKS
    for task in TASKS:
        assert task.language in {"python", "node"}, task.name
        assert task.prompt.strip(), task.name
        assert task.reference_dir.is_dir(), task.name


def test_hidden_tests_and_reference_are_not_in_the_starter():
    for task in TASKS:
        if not task.starter_dir.is_dir():
            continue
        starter = {p.name for p in task.starter_dir.rglob("*")}
        assert not starter & {p.name for p in task.hidden_dir.iterdir()}, task.name


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.name)
def test_reference_solution_passes_its_hidden_tests(task, tmp_path, project_venv):
    result = grade(task, _workspace(tmp_path, task, project_venv, solved=True))
    assert result.status == "passed", f"{task.name}: {result.summary}\n{result.output}"


@pytest.mark.parametrize("task", TASKS, ids=lambda t: t.name)
def test_starter_alone_fails_its_hidden_tests(task, tmp_path, project_venv):
    result = grade(task, _workspace(tmp_path, task, project_venv, solved=False))
    assert result.status == "failed", f"{task.name}: {result.summary}\n{result.output}"


def test_grading_ignores_the_projects_own_pytest_settings(tmp_path, project_venv):
    task = next(t for t in TASKS if t.name == "temperature-table")
    workspace = _workspace(tmp_path, task, project_venv, solved=True)
    (workspace / "pytest.ini").write_text("[pytest]\naddopts = --no-such-option\n")
    assert grade(task, workspace).passed


def test_a_task_with_no_collected_hidden_tests_is_an_error(tmp_path, project_venv):
    root = tmp_path / "tasks" / "empty-tests"
    (root / "hidden_tests").mkdir(parents=True)
    (root / "task.md").write_text("Do nothing.\n")
    (root / "hidden_tests" / "test_nothing.py").write_text("# no tests here\n")
    task = bench_tasks.load_task(root)
    workspace = tmp_path / "ws"
    workspace.mkdir()
    project_venv(workspace)
    result = grade(task, workspace)
    assert result.status == "error"


def test_task_folders_must_have_the_required_shape(tmp_path):
    (tmp_path / "no-prompt" / "hidden_tests").mkdir(parents=True)
    with pytest.raises(BenchTaskError, match="task.md"):
        load_tasks(tmp_path)


def test_task_set_version_and_hash():
    assert bench_tasks.task_set_version() == (BUILTIN_TASKS_DIR / "VERSION").read_text().strip()
    assert bench_tasks.task_set_hash() == bench_tasks.task_set_hash()
    assert len(bench_tasks.task_set_hash()) == 12


def test_a_custom_task_set_without_version_is_custom(tmp_path):
    assert bench_tasks.task_set_version(tmp_path) == "custom"
