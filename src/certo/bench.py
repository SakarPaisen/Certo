"""`certo bench`: run a benchmark file and record every run.

For each task × arm × repeat: a fresh temporary workspace with only the
task's starter files; the arm's strategy runs the normal Certo pipeline on
`task.md`; then the hidden tests are copied in and run in the project's own
environment. One JSON file per run lands in `<out>/runs/`, so an
interrupted benchmark keeps what it has and `--resume` continues it.

Runs are one at a time by default (a local GPU serves one model at a
time); `--parallel N` is allowed only when every arm uses cloud models.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .bench_config import DEFAULT_BENCH_FILE, Arm, BenchConfig, BenchConfigError, load_bench_config
from .bench_report import arm_rows, write_report
from .bench_strategies import STRATEGIES, RunContext
from .bench_tasks import (
    BUILTIN_TASKS_DIR,
    BenchTask,
    BenchTaskError,
    grade,
    load_tasks,
    prepare_workspace,
    task_set_hash,
    task_set_version,
)
from .model_pricing import (
    ESTIMATE_INPUT_TOKENS,
    ESTIMATE_OUTPUT_TOKENS,
    estimate_run_cost,
    is_local,
)

DEFAULT_RESULTS_DIR = "bench-results"
# Verdicts where the agent didn't finish on its own, so it made no claim.
_NO_CLAIM_VERDICTS = ("stuck", "budget_exhausted", "confirmation_required")
_SNAPSHOT_IGNORE = shutil.ignore_patterns(
    ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache"
)


@dataclass(frozen=True)
class PlannedRun:
    arm: Arm
    task: BenchTask
    repeat: int

    @property
    def run_id(self) -> str:
        return f"{self.arm.name}__{self.task.name}__r{self.repeat}"


def plan_runs(cfg: BenchConfig) -> list[PlannedRun]:
    """Repeat-major order, so a stopped benchmark has a little of every arm
    and task instead of all repeats of the first ones."""
    return [
        PlannedRun(arm, task, repeat)
        for repeat in range(1, cfg.repeats + 1)
        for task in cfg.tasks
        for arm in cfg.arms
    ]


def hardware_hint() -> dict[str, Any]:
    """Enough about this machine to compare numbers from different ones."""
    hint: dict[str, Any] = {
        "system": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }

    def probe(command: list[str]) -> str:
        try:
            out = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return ""
        return out.stdout.strip() if out.returncode == 0 else ""

    if sys.platform == "darwin":
        hint["cpu"] = probe(["sysctl", "-n", "machdep.cpu.brand_string"])
        memory = probe(["sysctl", "-n", "hw.memsize"])
        if memory.isdigit():
            hint["memory_gb"] = round(int(memory) / 2**30)
    elif os.path.isfile("/proc/meminfo"):
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    hint["memory_gb"] = round(int(line.split()[1]) / 2**20)
    if shutil.which("nvidia-smi"):
        gpus = probe(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"])
        if gpus:
            hint["gpu"] = gpus.replace("\n", "; ")
    return {k: v for k, v in hint.items() if v not in ("", None)}


def _write_json(path: Path, data: Any) -> None:
    """Write via a temporary file, so a crash never leaves half a file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def execute_run(
    planned: PlannedRun,
    cfg: BenchConfig,
    out_dir: Path,
    stream: Callable[..., Any],
) -> dict[str, Any]:
    """One isolated run: prepare, run the strategy, grade, record."""
    workspace = tempfile.mkdtemp(prefix="certo-bench-")
    isolation = tempfile.mkdtemp(prefix="certo-bench-iso-")
    try:
        prepare_workspace(planned.task, workspace)
        strategy = STRATEGIES[planned.arm.strategy]
        started_at = _now()
        start = time.monotonic()
        attempt, error = None, None
        try:
            attempt = strategy.run(
                RunContext(planned.task.prompt, workspace, cfg.catalog, isolation, stream),
                planned.arm.params,
            )
        except Exception as exc:  # noqa: BLE001 - recorded; the benchmark goes on
            error = f"{type(exc).__name__}: {exc}"
        wall = time.monotonic() - start
        graded = grade(planned.task, workspace)
        snapshot = out_dir / "workspaces" / planned.run_id
        if snapshot.exists():
            shutil.rmtree(snapshot)
        shutil.copytree(workspace, snapshot, ignore=_SNAPSHOT_IGNORE, symlinks=True)
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
        shutil.rmtree(isolation, ignore_errors=True)

    verdict = attempt.verification_state if attempt else None
    summary = attempt.run_summary if attempt else None
    claimed = attempt is not None and verdict not in _NO_CLAIM_VERDICTS
    names = list(attempt.models_used) if attempt else planned.arm.models
    record = {
        "run_id": planned.run_id,
        "arm": planned.arm.name,
        "strategy": planned.arm.strategy,
        "models": [{"name": n, "model": cfg.catalog[n].model} for n in names],
        "task": planned.task.name,
        "repeat": planned.repeat,
        "verdict": verdict,
        "agent_claimed_done": claimed,
        "hidden_tests": {
            "status": graded.status,
            "passed": graded.passed,
            "summary": graded.summary,
        },
        # Certo said verified, but the hidden tests failed.
        "fooled": verdict == "verified" and not graded.passed,
        # The agent claimed it was done, and Certo did not say verified.
        "caught": claimed and verdict != "verified",
        # Certo did not say verified, but the hidden tests passed: the work
        # was right and Certo couldn't confirm it (e.g. no tests to run).
        "unconfirmed_pass": verdict != "verified" and graded.passed,
        "wall_seconds": round(wall, 1),
        "tokens_in": summary.prompt_tokens if summary else 0,
        "tokens_out": summary.completion_tokens if summary else 0,
        "tokens_cached": summary.cache_read_tokens if summary else 0,
        "cost": round(summary.total_cost, 6) if summary else 0.0,
        "cost_known": summary.cost_complete if summary else True,
        "retries_used": attempt.retries_used if attempt else 0,
        "error": error,
        "started_at": started_at,
        "finished_at": _now(),
        "certo_version": __version__,
    }
    _write_json(out_dir / "runs" / f"{planned.run_id}.json", record)
    return record


def load_records(out_dir: Path) -> list[dict[str, Any]]:
    runs = out_dir / "runs"
    if not runs.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(runs.glob("*.json"))]


def _format_seconds(seconds: float) -> str:
    minutes, secs = divmod(round(seconds), 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{seconds:.0f}s"


def _describe(record: dict[str, Any]) -> str:
    if record["error"]:
        outcome = f"error ({record['error']})"
    else:
        outcome = record["verdict"]
    hidden = "passed" if record["hidden_tests"]["passed"] else record["hidden_tests"]["status"]
    cost = f"${record['cost']:.4f}" if record["cost_known"] else "cost unknown"
    return f"{outcome}; hidden tests {hidden}; {_format_seconds(record['wall_seconds'])}; {cost}"


def _print_plan(cfg: BenchConfig, todo: list[PlannedRun], total: int, out_dir: Path) -> None:
    print("Benchmark plan")
    version = task_set_version(cfg.tasks_dir)
    print(
        f"  Tasks: {len(cfg.tasks)} (task set {version})   Arms: {len(cfg.arms)}   "
        f"Repeats: {cfg.repeats}   Runs: {total}"
        + (f" ({len(todo)} left to run)" if len(todo) != total else "")
    )
    estimate, unknown = 0.0, []
    for arm in cfg.arms:
        runs = sum(1 for p in todo if p.arm.name == arm.name)
        parts = []
        for name in arm.models:
            entry = cfg.catalog[name]
            per_run = estimate_run_cost(entry)
            if per_run == 0.0:
                price = "local, no cost"
            elif per_run is None:
                price = "price unknown"
                unknown.append(name)
            else:
                price = f"~${per_run:.2f} per run"
                estimate += per_run * runs
            parts.append(f"{name} ({entry.model}, {price})")
        print(f"  {arm.name}: {arm.strategy}, {'; '.join(parts)}, {runs} run(s)")
    line = f"  Estimated cost: ~${estimate:.2f}"
    line += (
        f" (rough: assumes ~{ESTIMATE_INPUT_TOKENS // 1000}k input and "
        f"~{ESTIMATE_OUTPUT_TOKENS // 1000}k output tokens per run)"
    )
    if unknown:
        line += f"; no price known for {', '.join(sorted(set(unknown)))}"
    print(line)
    for warning in cfg.catalog_warnings:
        print(f"  Warning (models.yaml): {warning}")
    print(f"  Results: {out_dir}")


def _confirm(yes: bool, interactive: bool) -> bool:
    if yes:
        return True
    if not interactive:
        print("Not a terminal, so nothing was started: add --yes to run the benchmark.")
        return False
    try:
        answer = input("Start? [y/N] ").strip().lower()
    except EOFError:
        answer = ""
    return answer in ("y", "yes")


def _resolve_out_dir(args: argparse.Namespace) -> Path:
    if args.out:
        return Path(args.out)
    if args.resume:
        root = Path(DEFAULT_RESULTS_DIR)
        found = sorted(p for p in root.glob("*") if (p / "meta.json").is_file())
        if not found:
            raise BenchConfigError(
                f"--resume: no earlier results in ./{DEFAULT_RESULTS_DIR}; pass --out DIR."
            )
        return found[-1]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(DEFAULT_RESULTS_DIR) / stamp


def _meta(cfg: BenchConfig) -> dict[str, Any]:
    builtin = Path(cfg.tasks_dir) == BUILTIN_TASKS_DIR
    return {
        "certo_version": __version__,
        "date": _now(),
        "hardware": hardware_hint(),
        "task_set": {
            "version": task_set_version(cfg.tasks_dir),
            "hash": task_set_hash(cfg.tasks_dir),
            "source": "bundled" if builtin else cfg.tasks_dir,
        },
        "bench_file": cfg.path,
        "config": cfg.fingerprint(),
    }


def _check_out_dir(cfg: BenchConfig, out_dir: Path, resume: bool) -> None:
    """Refuse a results folder that doesn't fit, before anything is asked."""
    meta_path = out_dir / "meta.json"
    if resume:
        if not meta_path.is_file():
            raise BenchConfigError(f"--resume: {out_dir} has no earlier benchmark results.")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("config") != cfg.fingerprint() or meta.get("task_set", {}).get(
            "hash"
        ) != task_set_hash(cfg.tasks_dir):
            raise BenchConfigError(
                f"--resume: {out_dir} was made with different tasks, arms, repeats or "
                "models. Use a new --out folder, or restore the original bench file."
            )
    elif meta_path.is_file():
        raise BenchConfigError(
            f"{out_dir} already has benchmark results. Add --resume to continue them, "
            "or choose another --out folder."
        )


def _init_out_dir(cfg: BenchConfig, out_dir: Path) -> None:
    (out_dir / "runs").mkdir(parents=True, exist_ok=True)
    if not (out_dir / "meta.json").is_file():
        _write_json(out_dir / "meta.json", _meta(cfg))


def _default_stream(task: str, *, cfg) -> Any:
    from .runner import stream_task

    return stream_task(task, cfg=cfg)


def run_benchmark(
    cfg: BenchConfig,
    out_dir: Path,
    todo: list[PlannedRun],
    *,
    total: int,
    parallel: int = 1,
    max_cost: float | None = None,
    stream: Callable[..., Any] = _default_stream,
) -> tuple[list[dict[str, Any]], bool]:
    """Run `todo`; return (new records, stopped by --max-cost)."""
    lock = threading.Lock()
    spent = sum(r["cost"] for r in load_records(out_dir))
    done = total - len(todo)
    records: list[dict[str, Any]] = []
    stopped = False

    def one(planned: PlannedRun) -> None:
        nonlocal spent, done, stopped
        with lock:
            if max_cost is not None and spent >= max_cost:
                stopped = True
                return
        record = execute_run(planned, cfg, out_dir, stream)
        with lock:
            spent += record["cost"]
            done += 1
            records.append(record)
            print(
                f"[{done}/{total}] {planned.arm.name} · {planned.task.name} · "
                f"r{planned.repeat}: {_describe(record)}",
                flush=True,
            )

    if parallel <= 1:
        for planned in todo:
            one(planned)
            if stopped:
                break
    else:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = [pool.submit(one, p) for p in todo]
            try:
                for future in futures:
                    future.result()
            except KeyboardInterrupt:
                for future in futures:
                    future.cancel()
                raise
    return records, stopped


def build_bench_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certo bench",
        description=(
            "Compare models and strategies on Certo's bundled tasks, each graded by "
            "hidden tests the agent never sees. Models are named from models.yaml; "
            ".env is never read."
        ),
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_BENCH_FILE,
        help=f"The benchmark file (default: {DEFAULT_BENCH_FILE}).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help=f"Results folder (default: ./{DEFAULT_RESULTS_DIR}/<date-time>).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Continue an interrupted benchmark in --out (default: the latest results "
        "folder), skipping runs already recorded.",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        metavar="N",
        help="Run N at a time. Only when every arm uses cloud models (default: 1).",
    )
    parser.add_argument(
        "--max-cost",
        type=float,
        default=None,
        metavar="USD",
        help="Stop starting new runs once the recorded cost reaches USD; results so far are kept.",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Start without asking to confirm the plan."
    )
    parser.add_argument(
        "--list-tasks", action="store_true", help="List the tasks and exit, with no model."
    )
    parser.add_argument(
        "--check-tasks",
        action="store_true",
        help="Check every task with no model: its reference solution must pass its hidden "
        "tests and its starter alone must fail them.",
    )
    return parser


def _tasks_dir_from(config_path: str) -> str:
    """The task folder for --list-tasks/--check-tasks: the bench file's
    tasks_dir if the file exists and sets one, else the bundled set."""
    import yaml

    path = Path(config_path)
    if path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("tasks_dir"), str):
            return raw["tasks_dir"]
    return str(BUILTIN_TASKS_DIR)


def _list_tasks(tasks_dir: str) -> int:
    tasks = load_tasks(tasks_dir)
    print(
        f"Task set {task_set_version(tasks_dir)} ({task_set_hash(tasks_dir)}), {len(tasks)} tasks:"
    )
    for task in tasks:
        first = next((ln.lstrip("# ").strip() for ln in task.prompt.splitlines() if ln.strip()), "")
        print(f"  {task.name:<22} {task.language:<7} {first}")
    return 0


def check_tasks(tasks_dir: str) -> list[str]:
    """Problems with a task set, or [] when every task is valid."""
    problems = []
    for task in load_tasks(tasks_dir):
        for solved, wanted in ((True, "passed"), (False, "failed")):
            workspace = tempfile.mkdtemp(prefix="certo-bench-check-")
            try:
                prepare_workspace(task, workspace, solved=solved)
                result = grade(task, workspace)
            finally:
                shutil.rmtree(workspace, ignore_errors=True)
            if result.status != wanted:
                which = "reference solution" if solved else "starter alone"
                problems.append(
                    f"{task.name}: the {which} should have {wanted} its hidden tests, but "
                    f"grading gave {result.status} ({result.summary})"
                )
    return problems


def _check_tasks(tasks_dir: str) -> int:
    problems = check_tasks(tasks_dir)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"All {len(load_tasks(tasks_dir))} tasks are valid.")
    return 0


def bench_main(
    argv: list[str],
    *,
    stream: Callable[..., Any] = _default_stream,
    interactive: bool | None = None,
) -> int:
    args = build_bench_parser().parse_args(argv)
    on_terminal = sys.stdin.isatty() if interactive is None else interactive
    try:
        if args.list_tasks:
            return _list_tasks(_tasks_dir_from(args.config))
        if args.check_tasks:
            return _check_tasks(_tasks_dir_from(args.config))
        if args.parallel < 1:
            raise BenchConfigError("--parallel must be at least 1.")
        if args.max_cost is not None and args.max_cost <= 0:
            raise BenchConfigError("--max-cost must be greater than 0.")
        cfg = load_bench_config(args.config)
        local = sorted({n for a in cfg.arms for n in a.models if is_local(cfg.catalog[n])})
        if args.parallel > 1 and local:
            raise BenchConfigError(
                f"--parallel needs cloud models only; {', '.join(local)} runs locally, and "
                "a local server serves one model at a time. Run without --parallel."
            )
        out_dir = _resolve_out_dir(args)
        planned = plan_runs(cfg)
        recorded = {r["run_id"] for r in load_records(out_dir)} if args.resume else set()
        todo = [p for p in planned if p.run_id not in recorded]
        _check_out_dir(cfg, out_dir, args.resume)
    except (BenchConfigError, BenchTaskError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    _print_plan(cfg, todo, len(planned), out_dir)
    if not todo:
        print("Every run is already recorded.")
    elif not _confirm(args.yes, on_terminal):
        return 1
    _init_out_dir(cfg, out_dir)

    interrupted = stopped = False
    try:
        _, stopped = run_benchmark(
            cfg,
            out_dir,
            todo,
            total=len(planned),
            parallel=args.parallel,
            max_cost=args.max_cost,
            stream=stream,
        )
    except KeyboardInterrupt:
        interrupted = True
    records = load_records(out_dir)
    finish_report(cfg, out_dir, records)
    if stopped:
        print(f"Stopped: the recorded cost reached --max-cost ${args.max_cost:.2f}.")
    if interrupted:
        print(
            "Interrupted. Finished runs are kept; continue with: certo bench --resume "
            f"--out {out_dir}"
        )
        return 130
    left = len(planned) - len(records)
    if left:
        print(f"{left} run(s) not done. Continue with: certo bench --resume --out {out_dir}")
    return 0


def finish_report(cfg: BenchConfig, out_dir: Path, records: list[dict[str, Any]]) -> None:
    """Write results.md and results.csv, and print the per-arm summary."""
    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    markdown = write_report(out_dir)
    print(f"\n{len(records)}/{len(plan_runs(cfg))} runs recorded.")
    for row in arm_rows(meta, records):
        print(
            f"  {row['Arm']}: hidden tests passed {row['Hidden tests passed']}, verified "
            f"{row['Verified']}, fooled {row['Fooled']}, caught {row['Caught']}, "
            f"cost {row['Cost']}"
        )
    print(f"Results: {markdown} (and results.csv)")
