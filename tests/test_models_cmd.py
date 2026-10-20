"""`certo models update`: the three-way plan, the text edit that keeps
comments, and the command. No model and no network."""

from __future__ import annotations

import pytest
import yaml
from test_init_cmd import Script

from certo import cli
from certo.models_cmd import apply, models_main, plan

_BASE = """# My list. This comment must survive.
models:
  # Local
  - name: local
    model: ollama/qwen3-coder:30b
    ratings: {reasoning: 1, code: 1, cost: 5}

  - name: old-cloud
    model: openai/gpt-4.1
    ratings: {reasoning: 3, code: 3, cost: 3}

  - name: cloud
    model: openai/gpt-6-luna   # an inline comment
    ratings: {reasoning: 4, code: 4, cost: 4}
"""

# The new example: `local` re-rated, `old-cloud` gone, `strong` new.
_EXAMPLE = """# The example header.
models:
  # Local
  - name: local
    model: ollama/qwen3-coder:30b
    ratings: {reasoning: 1, code: 2, cost: 5}

  - name: cloud
    model: openai/gpt-6-luna   # an inline comment
    ratings: {reasoning: 4, code: 4, cost: 4}

  - name: strong
    model: anthropic/claude-opus-5-5
    ratings: {reasoning: 5, code: 5, cost: 1}
"""


def _kinds(changes):
    return {c.name: c.kind for c in changes}


def test_certos_changes_are_offered_and_the_users_are_kept():
    yours = _BASE.replace("{reasoning: 4, code: 4, cost: 4}", "{reasoning: 4, code: 5, cost: 4}")
    yours += "\n  - name: mine\n    model: ollama/mine:7b\n    ratings: {code: 2}\n"

    changes, notes = plan(yours, _BASE, _EXAMPLE, used=set())

    assert _kinds(changes) == {"local": "changed", "strong": "new", "old-cloud": "removed"}
    local = next(c for c in changes if c.name == "local")
    assert local.details == ["ratings: code 1 -> 2"]
    assert "cloud: your changes" in notes
    assert "mine: yours" in notes


def test_an_entry_both_changed_is_asked_about():
    yours = _BASE.replace("{reasoning: 1, code: 1, cost: 5}", "{reasoning: 2, code: 1, cost: 5}")

    changes, _notes = plan(yours, _BASE, _EXAMPLE, used=set())

    assert _kinds(changes)["local"] == "both"


def test_without_a_base_every_difference_is_asked_and_nothing_is_removed():
    changes, notes = plan(_BASE, None, _EXAMPLE, used=set())

    assert _kinds(changes) == {"local": "both", "strong": "new"}
    assert "old-cloud: yours" in notes


def test_a_model_models_yaml_uses_is_never_removed():
    changes, notes = plan(_BASE, _BASE, _EXAMPLE, used={"old-cloud"})

    assert "old-cloud" not in _kinds(changes)
    assert "old-cloud: no longer in the example, but models.yaml uses it" in notes


def test_a_model_you_removed_is_not_added_again():
    yours = _BASE.replace(
        "  - name: old-cloud\n    model: openai/gpt-4.1\n    ratings: {reasoning: 3, code: 3, cost: 3}\n\n",
        "",
    )
    example = (
        _EXAMPLE + "\n  - name: old-cloud\n    model: openai/gpt-4.1\n    ratings: {code: 3}\n"
    )

    changes, notes = plan(yours, _BASE, example, used=set())

    assert "old-cloud" not in _kinds(changes)
    assert "old-cloud: removed by you, not added again" in notes


def test_apply_keeps_comments_and_puts_new_models_inside_the_models_list():
    # A list from before 0.1.20 still has a section after its models.
    yours = _BASE + "\ntask_profiles:\n  default:\n    weights: {code: 1}\n"
    changes, _notes = plan(yours, _BASE, _EXAMPLE, used=set())

    result = apply(yours, _EXAMPLE, changes)

    assert "# My list. This comment must survive." in result
    assert "  # Local\n" in result
    assert "openai/gpt-6-luna   # an inline comment" in result
    data = yaml.safe_load(result)
    assert [m["name"] for m in data["models"]] == ["local", "cloud", "strong"]
    assert data["models"][0]["ratings"]["code"] == 2
    assert data["task_profiles"] == {"default": {"weights": {"code": 1}}}


def test_apply_refuses_a_layout_it_cant_edit_safely():
    # Entries at column 0: not the example's layout, so not found as blocks.
    flat = "models:\n- name: local\n  model: ollama/qwen3-coder:30b\n  ratings: {code: 1}\n"
    changes, _notes = plan(flat, flat, _EXAMPLE, used=set())

    with pytest.raises(ValueError):
        apply(flat, _EXAMPLE, changes)


# --- the command -----------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    config = tmp_path / "config"
    (config / "certo").mkdir(parents=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config))
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    folder = config / "certo"
    (folder / "models_list.yaml").write_text(_BASE)
    (folder / ".models_list.base.yaml").write_text(_BASE)
    example = tmp_path / "example.yaml"
    example.write_text(_EXAMPLE)
    return folder, str(example)


def _update(example, answers=(), argv=("update",), interactive=True):
    script = Script(answers=answers)
    code = models_main(
        list(argv), prompter=script.prompter(), interactive=interactive, example=example
    )
    return code, script.text


def test_all_changes_are_applied_with_a_backup_and_a_new_base(files):
    folder, example = files

    code, text = _update(example, answers=[""])  # "All 3", the default

    assert code == 0
    assert "Updated " in text and "3 change(s)" in text
    names = [m["name"] for m in yaml.safe_load((folder / "models_list.yaml").read_text())["models"]]
    assert names == ["local", "cloud", "strong"]
    assert (folder / "models_list.yaml.bak").read_text() == _BASE
    assert (folder / ".models_list.base.yaml").read_text() == _EXAMPLE


def test_one_by_one_applies_only_the_confirmed(files):
    folder, example = files

    # One by one: local yes, old-cloud no, strong yes (in the plan's order).
    code, _text = _update(example, answers=["2", "y", "y", "n"])

    assert code == 0
    names = {m["name"] for m in yaml.safe_load((folder / "models_list.yaml").read_text())["models"]}
    assert names == {"local", "cloud", "strong", "old-cloud"}


def test_without_a_terminal_nothing_is_written_unless_yes(files):
    folder, example = files

    code, text = _update(example, interactive=False)
    assert code == 0
    assert "Nothing was written" in text
    assert (folder / "models_list.yaml").read_text() == _BASE

    code, _text = _update(example, argv=("update", "--yes"), interactive=False)
    assert code == 0
    assert "strong" in (folder / "models_list.yaml").read_text()


def test_yes_keeps_your_version_of_an_entry_both_changed(files):
    folder, example = files
    mine = _BASE.replace("{reasoning: 1, code: 1, cost: 5}", "{reasoning: 2, code: 1, cost: 5}")
    (folder / "models_list.yaml").write_text(mine)

    _update(example, argv=("update", "--yes"), interactive=False)

    local = yaml.safe_load((folder / "models_list.yaml").read_text())["models"][0]
    assert local["ratings"] == {"reasoning": 2, "code": 1, "cost": 5}


def test_without_a_list_it_points_to_init_models(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "empty"))
    monkeypatch.chdir(tmp_path)

    code, text = _update(str(tmp_path / "x.yaml"))

    assert code == 1
    assert "Run certo init models" in text


def test_certo_models_is_a_subcommand(monkeypatch):
    seen = []
    monkeypatch.setattr("certo.models_cmd.models_main", lambda argv: seen.append(argv) or 0)

    assert cli.main(["models", "update", "--yes"]) == 0
    assert seen == [["update", "--yes"]]
