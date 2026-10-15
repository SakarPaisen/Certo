"""A heads-up before the agent edits a folder that already has files.

Printed by `cli.py` before a task starts, never a question: the agent edits
files in place, and the only undo a user has is their own version control.
So a git repository with uncommitted changes gets a warning (commit or
stash first), and a folder that isn't a git repository gets a one-line
note that its changes can't be rolled back with git. Empty folders and
`--project` folders Certo created itself get nothing.

Stdlib only, no SDK import.
"""

from __future__ import annotations

import os
import shutil
import subprocess

# One project name per line, in CERTO_PROJECTS_DIR: the `--project` folders
# Certo created. Kept beside the projects rather than inside one, so a
# generated project carries no Certo file of its own.
CREATED_PROJECTS_FILE = ".certo-created-projects"
_GIT_TIMEOUT_SECONDS = 10


def _created_list(projects_dir: str) -> str:
    return os.path.join(projects_dir, CREATED_PROJECTS_FILE)


def _project_key(project: str) -> str:
    return os.path.normpath(project).replace(os.sep, "/")


def record_created_project(projects_dir: str, project: str) -> None:
    """Remember that Certo created `projects_dir/project`."""
    if was_created_by_certo(projects_dir, project):
        return
    with open(_created_list(projects_dir), "a", encoding="utf-8") as f:
        f.write(_project_key(project) + "\n")


def was_created_by_certo(projects_dir: str, project: str) -> bool:
    try:
        with open(_created_list(projects_dir), encoding="utf-8") as f:
            names = {line.strip() for line in f}
    except OSError:
        return False
    return _project_key(project) in names


def _has_files(path: str) -> bool:
    try:
        with os.scandir(path) as entries:
            return any(True for _ in entries)
    except OSError:
        return False


def _git(path: str, *args: str) -> subprocess.CompletedProcess[str] | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        return subprocess.run(
            [git, "-C", path, *args],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def worktree_warning(path: str) -> str | None:
    """The message to print before the agent works in `path`, or None.

    Only changes under `path` count, so a task in a clean subfolder of a
    repository with changes elsewhere gets no warning.
    """
    if not _has_files(path):
        return None
    shown = os.path.abspath(path)
    inside = _git(path, "rev-parse", "--is-inside-work-tree")
    if inside is None:
        return (
            f"Note: git isn't available, so the agent's changes in {shown} "
            "can't be rolled back with git."
        )
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return (
            f"Note: {shown} isn't a git repository, so the agent's changes there "
            "can't be rolled back with git."
        )
    status = _git(path, "status", "--porcelain", "--", ".")
    if status is None or status.returncode != 0:
        return None
    changed = [line for line in status.stdout.splitlines() if line.strip()]
    if not changed:
        return None
    files = "1 file" if len(changed) == 1 else f"{len(changed)} files"
    return (
        f"Warning: {shown} has uncommitted changes ({files}). The agent will edit "
        "files here; commit or stash first if you want to be able to roll back."
    )
