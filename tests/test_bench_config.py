"""bench.yaml parsing, validation, and the strategy registry. No model."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from certo import bench_strategies
from certo.bench_config import BenchConfigError, load_bench_config
from certo.bench_strategies import STRATEGIES, AttemptResult, RunContext, run_config
from certo.bench_tasks import load_tasks

_REPO = Path(__file__).resolve().parent.parent

MODELS = """
models:
  - name: local-coder
    model: ollama/qwen3-coder:30b
    base_url: http://localhost:11434
    activated: false
  - name: cloud
    model: anthropic/claude-sonnet-5-5
    api_key: sk-test
    reasoning_effort: low
"""


def _write(tmp_path: Path, bench: str, models: str = MODELS) -> str:
    (tmp_path / "models.yaml").write_text(models)
    path = tmp_path / "bench.yaml"
    path.write_text(f"models_file: {tmp_path / 'models.yaml'}\n" + bench)
    return str(path)


VALID = """
tasks: all
repeats: 3
arms:
  - name: qwen-local
    strategy: single
    model: local-coder
  - name: sonnet
    strategy: single
    model: cloud
"""


def test_a_valid_file(tmp_path):
    cfg = load_bench_config(_write(tmp_path, VALID))
    assert cfg.repeats == 3
    assert [t.name for t in cfg.tasks] == [t.name for t in load_tasks()]
    assert [(a.name, a.strategy, a.models) for a in cfg.arms] == [
        ("qwen-local", "single", ["local-coder"]),
        ("sonnet", "single", ["cloud"]),
    ]


def test_activated_false_is_ignored_because_naming_a_model_is_explicit(tmp_path):
    cfg = load_bench_config(_write(tmp_path, VALID))
    assert cfg.catalog["local-coder"].activated is False
    assert cfg.arms[0].models == ["local-coder"]


def test_a_task_list_and_default_repeats(tmp_path):
    bench = "tasks: [page-ranges, slugify]\narms:\n  - {name: a, strategy: single, model: cloud}\n"
    cfg = load_bench_config(_write(tmp_path, bench))
    assert [t.name for t in cfg.tasks] == ["page-ranges", "slugify"]
    assert cfg.repeats == 1


def test_unknown_model_lists_the_catalog_names(tmp_path):
    bench = "arms:\n  - {name: a, strategy: single, model: gpt-9}\n"
    with pytest.raises(BenchConfigError, match="unknown model 'gpt-9'.*has: cloud, local-coder"):
        load_bench_config(_write(tmp_path, bench))


def test_unknown_strategy_lists_the_known_ones(tmp_path):
    bench = "arms:\n  - {name: a, strategy: cascade, models: [cloud]}\n"
    with pytest.raises(
        BenchConfigError, match="unknown strategy 'cascade'.*Known strategies: single"
    ):
        load_bench_config(_write(tmp_path, bench))


@pytest.mark.parametrize(
    "bench, message",
    [
        ("arms: []\n", "'arms' must be a non-empty list"),
        ("repeats: 0\narms:\n  - {name: a, strategy: single, model: cloud}\n", "'repeats'"),
        ("repeats: true\narms:\n  - {name: a, strategy: single, model: cloud}\n", "'repeats'"),
        ("tasks: [nope]\narms:\n  - {name: a, strategy: single, model: cloud}\n", "unknown task"),
        ("tasks: 3\narms:\n  - {name: a, strategy: single, model: cloud}\n", "'tasks' must be"),
        ("arms:\n  - {name: 'a b', strategy: single, model: cloud}\n", "needs a 'name'"),
        (
            (
                "arms:\n  - {name: a, strategy: single, model: cloud}\n"
                "  - {name: a, strategy: single, model: cloud}\n"
            ),
            "two arms are named 'a'",
        ),
        ("arms:\n  - {name: a, strategy: single}\n", "'model' must be a model name"),
        ("arms:\n  - {name: a, strategy: single, model: cloud, n: 3}\n", "unknown key"),
        ("arms:\n  - {name: a, strategy: single, model: cloud}\nrepeat: 2\n", "unknown key"),
    ],
)
def test_invalid_files_name_the_problem(tmp_path, bench, message):
    with pytest.raises(BenchConfigError, match=message):
        load_bench_config(_write(tmp_path, bench))


def test_missing_bench_file_says_what_to_do(tmp_path):
    with pytest.raises(BenchConfigError, match="bench.yaml.example"):
        load_bench_config(str(tmp_path / "bench.yaml"))


def test_missing_models_file_says_what_to_do(tmp_path):
    path = tmp_path / "bench.yaml"
    path.write_text(f"models_file: {tmp_path / 'nope.yaml'}\narms: []\n")
    with pytest.raises(BenchConfigError, match="models.yaml.example"):
        load_bench_config(str(path))


def test_the_shipped_example_is_valid_against_the_shipped_models_example(tmp_path):
    text = (_REPO / "bench.yaml.example").read_text()
    path = tmp_path / "bench.yaml"
    path.write_text(f"models_file: {_REPO / 'models.yaml.example'}\n" + text)
    cfg = load_bench_config(str(path))
    assert len(cfg.arms) == 2


def test_run_config_takes_everything_from_the_catalog_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("CERTO_LLM_MODEL", "openai/should-not-be-used")
    monkeypatch.setenv("CERTO_LLM_API_KEY", "sk-env")
    cfg = load_bench_config(_write(tmp_path, VALID))
    local = run_config(cfg.catalog["local-coder"], "/ws", "/iso")
    assert (local.model, local.api_key, local.base_url) == (
        "ollama/qwen3-coder:30b",
        None,
        "http://localhost:11434",
    )
    cloud = run_config(cfg.catalog["cloud"], "/ws", "/iso")
    assert (cloud.model, cloud.api_key, cloud.base_url, cloud.reasoning_effort) == (
        "anthropic/claude-sonnet-5-5",
        "sk-test",
        None,
        "low",
    )
    assert cloud.workspace == "/ws"
    assert cloud.skills_dir.startswith("/iso") and cloud.third_party_skills_lock.startswith("/iso")
    assert (cloud.model_selection, cloud.confirm_mode, cloud.interactive) == (
        "manual",
        "never",
        False,
    )


def test_single_strategy_runs_the_normal_pipeline_with_the_arm_model(tmp_path):
    cfg = load_bench_config(_write(tmp_path, VALID))
    seen = {}

    def fake_stream(task, *, cfg):
        seen.update(task=task, model=cfg.model)
        return SimpleNamespace(verification_state="verified", retries_used=1, run_summary=None)

    ctx = RunContext("do it", "/ws", cfg.catalog, "/iso", fake_stream)
    result = STRATEGIES["single"].run(ctx, cfg.arms[1].params)
    assert seen == {"task": "do it", "model": "anthropic/claude-sonnet-5-5"}
    assert result == AttemptResult("verified", 1, None, ("cloud",))


def test_a_new_strategy_is_one_registry_entry(tmp_path, monkeypatch):
    """The design promise: adding e.g. best_of needs no change elsewhere."""

    class BestOf:
        name = "best_of"
        description = "test only"

        def parse(self, arm, catalog, where):
            bench_strategies.reject_unknown_keys(arm, {"model", "n"}, where)
            return {
                "model": bench_strategies.model_name(arm, "model", catalog, where),
                "n": arm["n"],
            }

        def models(self, params):
            return [params["model"]]

        def run(self, ctx, params):
            raise NotImplementedError

    monkeypatch.setitem(STRATEGIES, "best_of", BestOf())
    bench = "arms:\n  - {name: b, strategy: best_of, model: cloud, n: 3}\n"
    cfg = load_bench_config(_write(tmp_path, bench))
    assert cfg.arms[0].params == {"model": "cloud", "n": 3}
    assert cfg.arms[0].models == ["cloud"]
