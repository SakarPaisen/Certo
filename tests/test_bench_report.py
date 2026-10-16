"""results.md and results.csv from a results folder. No model."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from certo.bench_report import render_markdown, write_report

META = {
    "certo_version": "0.1.6",
    "date": "2026-10-16T10:00:00+00:00",
    "hardware": {"system": "Darwin 25.6.0", "machine": "arm64", "cpu_count": 12, "memory_gb": 36},
    "task_set": {"version": "1", "hash": "abc123def456", "source": "bundled"},
    "bench_file": "/x/bench.yaml",
    "config": {
        "tasks": ["page-ranges", "slugify"],
        "repeats": 2,
        "arms": [
            {"name": "local", "strategy": "single", "model": "qwen"},
            {"name": "cloud", "strategy": "single", "model": "sonnet"},
        ],
        "arm_models": {"local": ["qwen"], "cloud": ["sonnet"]},
        "models": {"qwen": "ollama/qwen3-coder:30b", "sonnet": "anthropic/claude-sonnet-5-5"},
    },
}


def _record(arm, task, repeat, *, verdict, passed, cost=0.0, cost_known=True, error=None, wall=60):
    claimed = verdict not in (None, "stuck", "budget_exhausted", "confirmation_required")
    model = META["config"]["arm_models"][arm][0]
    return {
        "run_id": f"{arm}__{task}__r{repeat}",
        "arm": arm,
        "strategy": "single",
        "models": [{"name": model, "model": META["config"]["models"][model]}],
        "task": task,
        "repeat": repeat,
        "verdict": verdict,
        "agent_claimed_done": claimed,
        "hidden_tests": {
            "status": "passed" if passed else "failed",
            "passed": passed,
            "summary": "",
        },
        "fooled": verdict == "verified" and not passed,
        "caught": claimed and verdict != "verified",
        "unconfirmed_pass": verdict != "verified" and passed,
        "wall_seconds": wall,
        "tokens_in": 1000,
        "tokens_out": 100,
        "tokens_cached": 0,
        "cost": cost,
        "cost_known": cost_known,
        "retries_used": 0,
        "error": error,
    }


RECORDS = [
    _record("local", "page-ranges", 1, verdict="verified", passed=True, cost_known=False, wall=300),
    _record(
        "local", "page-ranges", 2, verdict="verified", passed=False, cost_known=False, wall=200
    ),
    _record("local", "slugify", 1, verdict="retry_exhausted", passed=False, cost_known=False),
    _record("local", "slugify", 2, verdict=None, passed=False, error="boom", cost_known=False),
    _record("cloud", "page-ranges", 1, verdict="verified", passed=True, cost=0.5, wall=90),
    _record("cloud", "page-ranges", 2, verdict="verified", passed=True, cost=0.5, wall=30),
    _record("cloud", "slugify", 1, verdict="inconclusive", passed=True, cost=0.25),
]


def _row(markdown: str, arm: str) -> list[str]:
    line = next(ln for ln in markdown.splitlines() if ln.startswith(f"| {arm} |"))
    return [cell.strip() for cell in line.strip("|").split("|")]


def test_arm_table():
    markdown = render_markdown(META, RECORDS)
    local = _row(markdown, "local")
    assert local[:3] == ["local", "single", "qwen (`ollama/qwen3-coder:30b`)"]
    assert local[3] == "1/4 (25%)"  # hidden tests passed
    assert local[4] == "2/4 (50%)"  # verified
    assert local[5:9] == ["1", "1", "0", "1"]  # fooled, caught, unconfirmed, errors
    assert local[9] == "2m 10s"  # median of 300, 200, 60, 60
    assert local[10] == "4,000 / 400"
    assert local[11] == "$0.0000 + unknown"
    cloud = _row(markdown, "cloud")
    assert cloud[3] == "3/3 (100%)"
    assert cloud[5:9] == ["0", "1", "1", "0"]
    assert cloud[11] == "$1.2500"


def test_header_records_where_and_what_was_run():
    markdown = render_markdown(META, RECORDS)
    assert "- Certo: 0.1.6" in markdown
    assert "- Task set: version 1 (`abc123def456`, bundled)" in markdown
    assert "- Hardware: Darwin 25.6.0, arm64, 12 CPUs, 36 GB RAM" in markdown
    assert "runs recorded: 7 of 8 (incomplete)" in markdown
    assert "Small samples: 4 runs per arm" in markdown


def test_per_task_table():
    markdown = render_markdown(META, RECORDS)
    assert "| page-ranges | 1/2 | 2/2 |" in markdown
    assert "| slugify | 0/2 | 1/1 |" in markdown


def test_write_report_writes_markdown_and_csv(tmp_path: Path):
    (tmp_path / "runs").mkdir()
    (tmp_path / "meta.json").write_text(json.dumps(META))
    for record in RECORDS:
        (tmp_path / "runs" / f"{record['run_id']}.json").write_text(json.dumps(record))
    markdown = write_report(tmp_path)
    assert markdown.read_text() == render_markdown(
        META,
        sorted(RECORDS, key=lambda r: (r["repeat"], r["task"], ["local", "cloud"].index(r["arm"]))),
    )
    with (tmp_path / "results.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 7
    first = rows[0]
    assert first["arm"] == "local" and first["task"] == "page-ranges"
    assert first["models"] == "qwen" and first["model_ids"] == "ollama/qwen3-coder:30b"
    assert first["hidden_passed"] == "True" and first["fooled"] == "False"


# --- escalate arms --------------------------------------------------------------------


def test_cost_per_solved_task():
    markdown = render_markdown(META, RECORDS)
    # cloud: $1.25 over 3 solved runs; local: no price known, 1 solved run.
    assert _row(markdown, "cloud")[-1] == "$0.4167"
    assert _row(markdown, "local")[-1] == "$0.0000 + unknown"


def test_cost_per_solved_task_with_nothing_solved():
    records = [_record("cloud", "slugify", 1, verdict="retry_exhausted", passed=False, cost=0.5)]
    assert _row(render_markdown(META, records), "cloud")[-1] == "-"


def _escalate_meta():
    meta = json.loads(json.dumps(META))
    meta["config"]["arms"].append({"name": "climb", "strategy": "escalate", "models": None})
    meta["config"]["arm_models"]["climb"] = ["qwen", "sonnet"]
    return meta


def _climb_record(task, repeat, final_rung, *, passed=True, error=None):
    record = _record("local", task, repeat, verdict="verified", passed=passed, error=error)
    names = ["qwen", "sonnet"]
    record.update(
        arm="climb",
        strategy="escalate",
        run_id=f"climb__{task}__r{repeat}",
        final_rung=final_rung,
        rungs=[
            {"rung": n, "name": names[n - 1], "final": n == final_rung}
            for n in range(1, (final_rung or 1) + 1)
        ],
    )
    return record


def test_which_rung_produced_the_final_result():
    records = RECORDS + [
        _climb_record("page-ranges", 1, 1),
        _climb_record("page-ranges", 2, 2),
        _climb_record("slugify", 1, 2),
        _climb_record("slugify", 2, None, passed=False, error="boom"),
    ]
    markdown = render_markdown(_escalate_meta(), records)

    assert "## Which rung produced the final result" in markdown
    assert (
        "- **climb:** rung 1 (qwen): 1/4, rung 2 (sonnet): 2/4, no result (error): 1/4"
        in markdown
    )


def test_single_arms_keep_their_columns_and_get_no_rung_section():
    markdown = render_markdown(META, RECORDS)
    header = next(ln for ln in markdown.splitlines() if ln.startswith("| Arm |"))
    assert header == (
        "| Arm | Strategy | Models | Hidden tests passed | Verified | Fooled | Caught | "
        "Unconfirmed passes | Errors | Median time | Tokens in / out | Cost | "
        "Cost per solved task |"
    )
    assert "Which rung produced the final result" not in markdown.split("## What the")[0]
