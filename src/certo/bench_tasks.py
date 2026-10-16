"""The benchmark's task set: load tasks, prepare a run's workspace, and grade
a finished workspace with the task's hidden tests.

A task is a folder:

    <name>/task.md        the prompt the agent sees
    <name>/starter/       optional starting files the agent sees
    <name>/hidden_tests/  the tests that decide the score; never shown to the agent
    <name>/reference/     a reference solution; never shown to the agent

The bundled set lives in `benchmark_tasks/` inside the package, like the
built-in skills. No SDK import here: loading, preparing and grading are all
testable without a model.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from .project_env import (
    CommandRunner,
    LocalRunner,
    available_modules,
    ensure_project_env,
    install_into_env,
)

BUILTIN_TASKS_DIR = Path(__file__).resolve().parent / "benchmark_tasks"
# Where grading copies the hidden tests in a finished workspace. A dot
# folder, so project detection and entry-point discovery never see it.
HIDDEN_DIR_NAME = ".certo_hidden_tests"
GRADE_TIMEOUT_SECONDS = 300
_OUTPUT_TAIL = 4000


class BenchTaskError(ValueError):
    """A task folder that doesn't have the required shape."""


@dataclass(frozen=True)
class BenchTask:
    name: str
    path: Path
    language: str  # "python" | "node"

    @property
    def prompt(self) -> str:
        return (self.path / "task.md").read_text(encoding="utf-8")

    @property
    def starter_dir(self) -> Path:
        return self.path / "starter"

    @property
    def hidden_dir(self) -> Path:
        return self.path / "hidden_tests"

    @property
    def reference_dir(self) -> Path:
        return self.path / "reference"


def _language(hidden: Path) -> str:
    names = [p.name for p in hidden.iterdir() if p.is_file()]
    if any(n.endswith(".py") for n in names):
        return "python"
    if any(n.endswith(".js") for n in names):
        return "node"
    raise BenchTaskError(f"{hidden} has no .py or .js test files")


def load_task(path: Path) -> BenchTask:
    if not (path / "task.md").is_file():
        raise BenchTaskError(f"{path} has no task.md")
    hidden = path / "hidden_tests"
    if not hidden.is_dir():
        raise BenchTaskError(f"{path} has no hidden_tests/ folder")
    return BenchTask(name=path.name, path=path, language=_language(hidden))


def load_tasks(tasks_dir: Path | str = BUILTIN_TASKS_DIR) -> list[BenchTask]:
    """Every task folder under `tasks_dir` (a folder with a task.md), by name."""
    root = Path(tasks_dir)
    if not root.is_dir():
        raise BenchTaskError(f"task folder not found: {root}")
    return [
        load_task(p) for p in sorted(root.iterdir()) if p.is_dir() and not p.name.startswith(".")
    ]


def task_set_version(tasks_dir: Path | str = BUILTIN_TASKS_DIR) -> str:
    """The `VERSION` file of a task set, or "custom" when it has none."""
    version_file = Path(tasks_dir) / "VERSION"
    if version_file.is_file():
        return version_file.read_text(encoding="utf-8").strip()
    return "custom"


def task_set_hash(tasks_dir: Path | str = BUILTIN_TASKS_DIR) -> str:
    """A short hash of every file in the task set, so results from two
    machines can be checked to use exactly the same tasks."""
    root = Path(tasks_dir)
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if "__pycache__" in path.parts or path.name == ".DS_Store":
            continue
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _copy_into(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)


def prepare_workspace(task: BenchTask, workspace: Path | str, *, solved: bool = False) -> None:
    """Fill `workspace` with the starter files, which is all the agent sees.
    `solved=True` adds the reference solution on top (task validation only)."""
    target = Path(workspace)
    target.mkdir(parents=True, exist_ok=True)
    _copy_into(task.starter_dir, target)
    if solved:
        _copy_into(task.reference_dir, target)


@dataclass(frozen=True)
class GradeResult:
    status: str  # "passed" | "failed" | "error" (couldn't grade at all)
    summary: str
    command: str = ""
    output: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "passed"


def _last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _copy_hidden_tests(task: BenchTask, workspace: Path) -> list[str]:
    hidden = workspace / HIDDEN_DIR_NAME
    if hidden.exists():
        shutil.rmtree(hidden)
    shutil.copytree(task.hidden_dir, hidden)
    suffix = ".py" if task.language == "python" else ".js"
    return sorted(str(p) for p in hidden.iterdir() if p.is_file() and p.name.endswith(suffix))


def _grade_python(task: BenchTask, workspace: Path, runner: CommandRunner) -> GradeResult:
    setup = ensure_project_env(str(workspace), runner, stop_at=str(workspace))
    if setup.env is None:
        return GradeResult("error", f"no project environment: {setup.unavailable_reason}")
    env = setup.env
    modules = available_modules(env, runner, str(workspace))
    if modules is None:
        return GradeResult("error", "the project environment's interpreter could not be run")
    if "pytest" not in modules:
        install = install_into_env(env, runner, "pytest", str(workspace))
        if install.returncode != 0:
            detail = _last_line(install.error or install.output) or "install failed"
            return GradeResult("error", f"could not install pytest for grading: {detail}")
    files = _copy_hidden_tests(task, workspace)
    hidden = workspace / HIDDEN_DIR_NAME
    # An ini file of our own: the project's pytest settings (addopts, plugins)
    # must not change how the hidden tests run.
    ini = hidden / "pytest.ini"
    ini.write_text("[pytest]\n", encoding="utf-8")
    command = [
        *env.python,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "-c",
        str(ini),
        "--rootdir",
        str(hidden),
        *files,
    ]
    extra = {
        **env.env_vars(runner.base_path()),
        "PYTHONPATH": str(workspace),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    result = runner.run(command, cwd=str(workspace), env=extra, timeout=GRADE_TIMEOUT_SECONDS)
    return _result(command, result, failed_codes=(1, 2))


def _grade_node(task: BenchTask, workspace: Path, runner: CommandRunner) -> GradeResult:
    node = runner.which("node")
    if node is None:
        return GradeResult("error", "node is not installed")
    files = _copy_hidden_tests(task, workspace)
    command = [node, "--test", *files]
    result = runner.run(command, cwd=str(workspace), timeout=GRADE_TIMEOUT_SECONDS)
    return _result(command, result, failed_codes=None)


def _result(command, result, *, failed_codes) -> GradeResult:
    shown = " ".join(command)
    output = result.output[-_OUTPUT_TAIL:]
    if result.timed_out:
        return GradeResult("failed", f"timed out after {GRADE_TIMEOUT_SECONDS}s", shown, output)
    if result.returncode is None:
        return GradeResult("error", f"could not run: {result.error}", shown, output)
    if result.returncode == 0:
        return GradeResult("passed", _summary(output), shown, output)
    if failed_codes is None or result.returncode in failed_codes:
        return GradeResult("failed", _summary(output), shown, output)
    return GradeResult("error", f"exit {result.returncode}: {_last_line(output)}", shown, output)


def _summary(output: str) -> str:
    """pytest's last line, or node's '# pass N' / '# fail N' counts."""
    counts = [
        line.strip()[2:]
        for line in output.splitlines()
        if line.strip().startswith(("# pass ", "# fail "))
    ]
    return ", ".join(counts) if counts else _last_line(output)


def grade(
    task: BenchTask, workspace: Path | str, runner: CommandRunner | None = None
) -> GradeResult:
    """Copy the hidden tests into `workspace` and run them in the project's
    own environment. Only these tests decide the score."""
    root = Path(os.path.abspath(workspace))
    runner = runner or LocalRunner()
    if task.language == "python":
        return _grade_python(task, root, runner)
    return _grade_node(task, root, runner)
