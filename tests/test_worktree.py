"""The note printed before the agent edits a folder that already has files.

Real temporary git repositories, no mocks of git itself. The CLI tests
monkeypatch only load_config and run_task, as tests/test_cli.py does.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest

from certo import cli, worktree
from certo.config import Config, load_config
from certo.runner import CompletionContract, TaskOutcome, TaskResult
from certo.worktree import worktree_warning

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def _git(path, *args):
    subprocess.run(
        ["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True,
        capture_output=True,
    )


def _repo(path):
    """A git repository with one committed file."""
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    (path / "app.py").write_text("print('hi')\n")
    _git(path, "add", "app.py")
    _git(path, "commit", "-q", "-m", "first")
    return path


# --- the message -----------------------------------------------------------------


def test_clean_repository_gets_no_warning(tmp_path):
    assert worktree_warning(str(_repo(tmp_path / "r"))) is None


def test_modified_file_in_a_repository_is_a_warning(tmp_path):
    repo = _repo(tmp_path / "r")
    (repo / "app.py").write_text("print('changed')\n")

    message = worktree_warning(str(repo))

    assert message.startswith(f"Warning: {repo} has uncommitted changes (1 file).")
    assert "commit or stash first" in message


def test_untracked_files_count_as_uncommitted(tmp_path):
    repo = _repo(tmp_path / "r")
    (repo / "notes.txt").write_text("new\n")
    (repo / "more.txt").write_text("new\n")

    assert "(2 files)" in worktree_warning(str(repo))


def test_only_changes_under_the_folder_count(tmp_path):
    repo = _repo(tmp_path / "r")
    (repo / "sub").mkdir()
    (repo / "sub" / "a.py").write_text("x = 1\n")
    _git(repo, "add", "sub")
    _git(repo, "commit", "-q", "-m", "sub")
    (repo / "app.py").write_text("print('changed elsewhere')\n")

    assert worktree_warning(str(repo / "sub")) is None
    assert worktree_warning(str(repo)) is not None


def test_folder_outside_git_gets_a_note(tmp_path):
    folder = tmp_path / "plain"
    folder.mkdir()
    (folder / "main.py").write_text("")

    message = worktree_warning(str(folder))

    assert message == (
        f"Note: {folder} isn't a git repository, so the agent's changes there "
        "can't be rolled back with git."
    )


def test_a_folder_with_only_certo_state_counts_as_empty(tmp_path):
    from certo.project_state import ensure_state_dir

    folder = tmp_path / "plain"
    folder.mkdir()
    ensure_state_dir(str(folder))

    assert worktree_warning(str(folder)) is None


def test_certo_state_is_not_an_uncommitted_change(tmp_path):
    from certo.project_state import ensure_state_dir

    _repo(tmp_path)
    ensure_state_dir(str(tmp_path))
    (tmp_path / ".certo" / "STATUS.md").write_text("x")

    assert worktree_warning(str(tmp_path)) is None


def test_empty_or_missing_folder_gets_nothing(tmp_path):
    (tmp_path / "empty").mkdir()
    assert worktree_warning(str(tmp_path / "empty")) is None
    assert worktree_warning(str(tmp_path / "missing")) is None


def test_freshly_initialized_empty_repository_has_files_but_no_changes(tmp_path):
    (tmp_path / "r").mkdir()
    _git(tmp_path / "r", "init", "-q")  # only .git inside

    assert worktree_warning(str(tmp_path / "r")) is None


# --- from the CLI ----------------------------------------------------------------


def _result():
    contract = CompletionContract(
        goal="", acceptance_criteria=[], verification_checks=[], limitations=[]
    )
    return TaskResult([], TaskOutcome(verification_state="verified", completion_contract=contract))


@pytest.fixture
def cli_run(monkeypatch, tmp_path):
    """Run `certo <argv>` with config from `env` and a fake agent that
    records whether it ran. Returns a function giving (exit code, stderr)."""

    def run(argv, capsys, **env):
        base = {"CERTO_LLM_MODEL": "openai/x", "CERTO_LLM_API_KEY": "k"}
        cfg: Config = load_config({**base, **env})
        ran = []
        monkeypatch.setattr(cli, "load_config", lambda: cfg)
        monkeypatch.setattr(cli, "run_task", lambda *a, **k: ran.append(True) or _result())
        code = cli.main(argv)
        assert ran == [True]  # never blocks the task
        return code, capsys.readouterr().err

    return run


def test_task_in_a_dirty_repository_prints_the_warning_and_still_runs(
    tmp_path, monkeypatch, capsys, cli_run
):
    repo = _repo(tmp_path / "r")
    (repo / "app.py").write_text("print('changed')\n")
    monkeypatch.chdir(repo)

    code, err = cli_run(["fix the bug"], capsys)

    assert code == 0
    assert "has uncommitted changes" in err


def test_the_warning_can_be_silenced(tmp_path, monkeypatch, capsys, cli_run):
    repo = _repo(tmp_path / "r")
    (repo / "app.py").write_text("print('changed')\n")
    monkeypatch.chdir(repo)

    _code, err = cli_run(["fix the bug"], capsys, CERTO_NO_WORKTREE_WARNING="1")

    assert err == ""


def test_project_folders_certo_created_get_no_warning(tmp_path, monkeypatch, capsys, cli_run):
    monkeypatch.chdir(tmp_path)
    projects = str(tmp_path / "projects")

    cli_run(["build it", "--project", "game"], capsys, CERTO_PROJECTS_DIR=projects)
    (tmp_path / "projects" / "game" / "game.py").write_text("")  # what the agent built
    _code, err = cli_run(["improve it", "--project", "game"], capsys, CERTO_PROJECTS_DIR=projects)

    assert err == ""
    assert worktree.was_created_by_certo(projects, "game")
    assert not (tmp_path / "projects" / "game" / worktree.CREATED_PROJECTS_FILE).exists()


def test_existing_project_folder_certo_did_not_create_gets_the_note(
    tmp_path, monkeypatch, capsys, cli_run
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "projects" / "mine").mkdir(parents=True)
    (tmp_path / "projects" / "mine" / "main.py").write_text("")

    _code, err = cli_run(
        ["improve it", "--project", "mine"], capsys, CERTO_PROJECTS_DIR=str(tmp_path / "projects")
    )

    assert "isn't a git repository" in err


@pytest.mark.parametrize("argv", [["verify", "."], ["check"], ["init", "--help"]])
def test_subcommands_never_print_it(tmp_path, monkeypatch, capsys, argv):
    repo = _repo(tmp_path / "r")
    (repo / "app.py").write_text("print('changed')\n")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "verify_main", lambda _argv: 0)
    monkeypatch.setattr(cli, "check_main", lambda _argv: 0)
    monkeypatch.setattr(cli, "worktree_warning", lambda _path: pytest.fail("no warning"))

    try:
        cli.main(argv)
    except SystemExit:
        pass  # init --help

    assert "uncommitted" not in capsys.readouterr().err
