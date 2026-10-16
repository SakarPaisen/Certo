"""`certo bench`: isolated runs, grading, recording, cost cap, resume and
interruption, with a fake model. No API key, no network."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from certo import bench
from certo.bench_config import load_bench_config
from certo.bench_tasks import load_tasks
from certo.model_catalog import ModelCatalogEntry
from certo.run_summary import ModelUsage, RunSummary

TASKS = {t.name: t for t in load_tasks()}

MODELS = """
models:
  - name: local-coder
    model: ollama/qwen3-coder:30b
    base_url: http://localhost:11434
  - name: cloud-a
    model: anthropic/test-model-a
    api_key: sk-a
  - name: cloud-b
    model: openai/test-model-b
    api_key: sk-b
"""


def _bench_file(tmp_path: Path, arms: str, tasks: str = "[temperature-table]", repeats: int = 1):
    (tmp_path / "models.yaml").write_text(MODELS)
    path = tmp_path / "bench.yaml"
    path.write_text(
        f"models_file: {tmp_path / 'models.yaml'}\ntasks: {tasks}\nrepeats: {repeats}\n"
        f"arms:\n{arms}"
    )
    return str(path)


ONE_ARM = "  - {name: a, strategy: single, model: cloud-a}\n"
TWO_ARMS = ONE_ARM + "  - {name: b, strategy: single, model: cloud-b}\n"


def _summary(cost: float = 0.25) -> RunSummary:
    return RunSummary(
        duration_seconds=1.0,
        models=(ModelUsage(model="m", prompt_tokens=1000, completion_tokens=50, cost=cost),),
    )


class FakeModel:
    """Stands in for runner.stream_task. `solve` copies the task's reference
    solution into the workspace; `verdicts` is consumed one per run."""

    def __init__(self, make_venv, *, solve=True, verdicts=("verified",), cost=0.25, raise_on=()):
        self.make_venv = make_venv
        self.solve = solve
        self.verdicts = list(verdicts)
        self.cost = cost
        self.raise_on = raise_on
        self.calls: list[SimpleNamespace] = []

    def __call__(self, task_text, *, cfg):
        self.calls.append(SimpleNamespace(task=task_text, cfg=cfg))
        call = len(self.calls)
        if call in self.raise_on:
            raise self.raise_on[call]
        workspace = Path(cfg.workspace)
        self.seen_files = sorted(p.name for p in workspace.iterdir())
        task = next(t for t in TASKS.values() if t.prompt == task_text)
        if self.solve:
            shutil.copytree(task.reference_dir, workspace, dirs_exist_ok=True)
        if task.language == "python":
            self.make_venv(workspace)
        verdict = self.verdicts[(call - 1) % len(self.verdicts)]
        return SimpleNamespace(
            verification_state=verdict, retries_used=1, run_summary=_summary(self.cost)
        )


def _run(path, out, model, *extra):
    return bench.bench_main(
        ["--config", path, "--out", str(out), "--yes", *extra], stream=model, interactive=False
    )


def _records(out: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((out / "runs").glob("*.json"))]


def test_a_run_is_isolated_graded_and_recorded(tmp_path, project_venv, capsys):
    model = FakeModel(project_venv)
    out = tmp_path / "out"
    assert _run(_bench_file(tmp_path, ONE_ARM), out, model) == 0
    call = model.calls[0]
    assert call.task == TASKS["temperature-table"].prompt
    assert call.cfg.model == "anthropic/test-model-a" and call.cfg.api_key == "sk-a"
    assert model.seen_files == []  # no starter for this task, no task.md, no hidden tests
    (record,) = _records(out)
    assert record["verdict"] == "verified"
    assert record["hidden_tests"]["passed"] is True
    assert (record["fooled"], record["caught"], record["agent_claimed_done"]) == (
        False,
        False,
        True,
    )
    assert (record["tokens_in"], record["tokens_out"], record["cost"]) == (1000, 50, 0.25)
    assert record["retries_used"] == 1
    assert record["models"] == [{"name": "cloud-a", "model": "anthropic/test-model-a"}]
    snapshot = out / "workspaces" / "a__temperature-table__r1"
    assert (snapshot / "temperature.py").is_file()
    assert not (snapshot / ".venv").exists()
    meta = json.loads((out / "meta.json").read_text())
    assert meta["task_set"]["source"] == "bundled"
    assert "| a | single | cloud-a" in (out / "results.md").read_text()
    assert (out / "results.csv").read_text().startswith("run_id,arm,")
    assert (
        "[1/1] a · temperature-table · r1: verified; hidden tests passed" in capsys.readouterr().out
    )


def test_starter_files_are_in_the_workspace(tmp_path, project_venv):
    model = FakeModel(project_venv)
    _run(_bench_file(tmp_path, ONE_ARM, tasks="[inventory-fix]"), tmp_path / "out", model)
    assert model.seen_files == ["inventory.py", "test_inventory.py"]


def test_fooled_when_certo_says_verified_but_hidden_tests_fail(tmp_path, project_venv):
    model = FakeModel(project_venv, solve=False, verdicts=("verified",))
    _run(_bench_file(tmp_path, ONE_ARM), tmp_path / "out", model)
    (record,) = _records(tmp_path / "out")
    assert record["hidden_tests"]["passed"] is False
    assert record["fooled"] is True and record["caught"] is False


def test_caught_when_the_agent_claimed_done_but_certo_did_not_verify(tmp_path, project_venv):
    model = FakeModel(project_venv, solve=False, verdicts=("retry_exhausted",))
    _run(_bench_file(tmp_path, ONE_ARM), tmp_path / "out", model)
    (record,) = _records(tmp_path / "out")
    assert record["caught"] is True and record["fooled"] is False
    assert record["unconfirmed_pass"] is False


def test_unconfirmed_pass_when_hidden_tests_pass_without_verified(tmp_path, project_venv):
    model = FakeModel(project_venv, solve=True, verdicts=("inconclusive",))
    _run(_bench_file(tmp_path, ONE_ARM), tmp_path / "out", model)
    (record,) = _records(tmp_path / "out")
    assert record["caught"] is True and record["unconfirmed_pass"] is True


def test_no_claim_when_the_run_was_stuck(tmp_path, project_venv):
    model = FakeModel(project_venv, solve=False, verdicts=("stuck",))
    _run(_bench_file(tmp_path, ONE_ARM), tmp_path / "out", model)
    (record,) = _records(tmp_path / "out")
    assert record["agent_claimed_done"] is False and record["caught"] is False


def test_a_crashing_run_is_recorded_and_the_benchmark_goes_on(tmp_path, project_venv):
    model = FakeModel(project_venv, raise_on={1: RuntimeError("provider down")})
    assert _run(_bench_file(tmp_path, TWO_ARMS), tmp_path / "out", model) == 0
    first, second = _records(tmp_path / "out")
    assert first["error"] == "RuntimeError: provider down"
    assert first["verdict"] is None and first["hidden_tests"]["passed"] is False
    assert second["error"] is None and second["hidden_tests"]["passed"] is True


def test_max_cost_stops_cleanly_and_keeps_results(tmp_path, project_venv, capsys):
    model = FakeModel(project_venv, cost=1.0)
    path = _bench_file(tmp_path, TWO_ARMS, repeats=2)
    assert _run(path, tmp_path / "out", model, "--max-cost", "1.5") == 0
    assert len(_records(tmp_path / "out")) == 2
    assert "Stopped: the recorded cost reached --max-cost $1.50." in capsys.readouterr().out


def test_interrupt_keeps_finished_runs_and_resume_continues(tmp_path, project_venv):
    path = _bench_file(tmp_path, TWO_ARMS, repeats=2)
    out = tmp_path / "out"
    model = FakeModel(project_venv, raise_on={2: KeyboardInterrupt()})
    assert _run(path, out, model) == 130
    assert [r["run_id"] for r in _records(out)] == ["a__temperature-table__r1"]

    model = FakeModel(project_venv)
    assert _run(path, out, model, "--resume") == 0
    assert len(model.calls) == 3
    assert len(_records(out)) == 4


def test_resume_refuses_a_different_benchmark(tmp_path, project_venv, capsys):
    out = tmp_path / "out"
    _run(_bench_file(tmp_path, ONE_ARM), out, FakeModel(project_venv))
    changed = _bench_file(tmp_path, TWO_ARMS)
    assert _run(changed, out, FakeModel(project_venv), "--resume") == 1
    assert "different tasks, arms, repeats or models" in capsys.readouterr().err


def test_an_existing_results_folder_is_not_overwritten(tmp_path, project_venv, capsys):
    out = tmp_path / "out"
    path = _bench_file(tmp_path, ONE_ARM)
    _run(path, out, FakeModel(project_venv))
    model = FakeModel(project_venv)
    assert _run(path, out, model) == 1
    assert model.calls == []
    assert "already has benchmark results" in capsys.readouterr().err


def test_without_a_terminal_it_needs_yes(tmp_path, project_venv, capsys):
    model = FakeModel(project_venv)
    path = _bench_file(tmp_path, ONE_ARM)
    code = bench.bench_main(
        ["--config", path, "--out", str(tmp_path / "out")], stream=model, interactive=False
    )
    assert code == 1 and model.calls == []
    assert "add --yes" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_the_plan_is_printed_first(tmp_path, project_venv, capsys):
    path = _bench_file(tmp_path, TWO_ARMS, tasks="[temperature-table, page-ranges]", repeats=3)
    bench.bench_main(["--config", path, "--out", str(tmp_path / "o")], interactive=False)
    out = capsys.readouterr().out
    assert "Tasks: 2 (task set 1)   Arms: 2   Repeats: 3   Runs: 12" in out
    assert "Estimated cost:" in out


def test_parallel_is_refused_with_a_local_model(tmp_path, project_venv, capsys):
    arms = "  - {name: q, strategy: single, model: local-coder}\n" + ONE_ARM
    assert (
        _run(
            _bench_file(tmp_path, arms),
            tmp_path / "out",
            FakeModel(project_venv),
            "--parallel",
            "2",
        )
        == 1
    )
    assert "local-coder runs locally" in capsys.readouterr().err


def test_parallel_runs_cloud_arms(tmp_path, project_venv):
    model = FakeModel(project_venv)
    path = _bench_file(tmp_path, TWO_ARMS, repeats=2)
    assert _run(path, tmp_path / "out", model, "--parallel", "2") == 0
    assert len(_records(tmp_path / "out")) == 4


def test_runs_are_ordered_repeat_first(tmp_path):
    cfg = load_bench_config(_bench_file(tmp_path, TWO_ARMS, repeats=2))
    assert [p.run_id for p in bench.plan_runs(cfg)] == [
        "a__temperature-table__r1",
        "b__temperature-table__r1",
        "a__temperature-table__r2",
        "b__temperature-table__r2",
    ]


@pytest.mark.parametrize(
    "model, base_url, local",
    [
        ("ollama/qwen3-coder:30b", "", True),
        ("openai/my-model", "http://192.168.1.50:8000", True),
        ("openai/my-model", "http://localhost:1234", True),
        ("deepseek/deepseek-chat", "https://api.deepseek.com", False),
        ("anthropic/claude-sonnet-5-5", "", False),
    ],
)
def test_is_local(model, base_url, local):
    entry = ModelCatalogEntry(name="x", model=model, base_url=base_url)
    assert bench.is_local(entry) is local


def test_list_tasks_needs_no_models(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert bench.bench_main(["--list-tasks"]) == 0
    out = capsys.readouterr().out
    assert "9 tasks" in out and "wordle-score" in out


def test_check_tasks_reports_a_broken_task(tmp_path, monkeypatch):
    broken = tmp_path / "tasks" / "broken"
    shutil.copytree(TASKS["temperature-table"].path, broken)
    # The "reference" now fails its own hidden tests.
    (broken / "reference" / "temperature.py").write_text(
        "def celsius_to_fahrenheit_table(start, stop, step):\n    return []\n"
    )
    monkeypatch.setattr(
        bench, "grade", lambda task, ws: SimpleNamespace(status="failed", summary="1 failed")
    )
    problems = bench.check_tasks(str(tmp_path / "tasks"))
    expected = (
        "broken: the reference solution should have passed its hidden tests, but grading "
        "gave failed (1 failed)"
    )
    assert problems == [expected]
