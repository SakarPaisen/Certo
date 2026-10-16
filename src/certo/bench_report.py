"""Turn a benchmark results folder into `results.md` and `results.csv`.

Works from the folder alone (`meta.json` plus `runs/*.json`), so an
interrupted or resumed benchmark can always be reported. Pure: no SDK, no
model.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path
from typing import Any

CSV_FIELDS = (
    "run_id",
    "arm",
    "strategy",
    "models",
    "model_ids",
    "task",
    "repeat",
    "verdict",
    "agent_claimed_done",
    "hidden_status",
    "hidden_passed",
    "fooled",
    "caught",
    "unconfirmed_pass",
    "wall_seconds",
    "tokens_in",
    "tokens_out",
    "tokens_cached",
    "cost",
    "cost_known",
    "retries_used",
    "final_rung",
    "error",
)


def _rate(count: int, total: int) -> str:
    return f"{count}/{total} ({count / total:.0%})" if total else "0/0"


def _seconds(seconds: float) -> str:
    minutes, secs = divmod(round(seconds), 60)
    return f"{minutes}m {secs:02d}s" if minutes else f"{round(seconds)}s"


def _cost(records: list[dict[str, Any]]) -> str:
    total = sum(r["cost"] for r in records)
    if all(r["cost_known"] for r in records):
        return f"${total:.4f}"
    return f"${total:.4f} + unknown"


def _cost_per_solved(records: list[dict[str, Any]]) -> str:
    """Total cost divided by the runs whose hidden tests passed."""
    solved = sum(r["hidden_tests"]["passed"] for r in records)
    if not solved:
        return "-"
    per = sum(r["cost"] for r in records) / solved
    return f"${per:.4f}" + ("" if all(r["cost_known"] for r in records) else " + unknown")


def rung_shares(records: list[dict[str, Any]]) -> str:
    """For an escalate arm: how often each rung gave the final result, for
    example "rung 1 (qwen-local): 4/9, rung 2 (gpt-luna): 5/9"."""
    counts: dict[tuple[int, str], int] = {}
    no_result = 0
    for r in records:
        final = next((g for g in r.get("rungs", []) if g.get("final")), None)
        if final is None:
            no_result += 1
            continue
        key = (final["rung"], final["name"])
        counts[key] = counts.get(key, 0) + 1
    total = len(records)
    parts = [f"rung {n} ({name}): {c}/{total}" for (n, name), c in sorted(counts.items())]
    if no_result:
        parts.append(f"no result (error): {no_result}/{total}")
    return ", ".join(parts) or "-"


def arm_rows(meta: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, str]]:
    models = meta["config"]["models"]
    rows = []
    for arm in meta["config"]["arms"]:
        mine = [r for r in records if r["arm"] == arm["name"]]
        names = meta["config"]["arm_models"][arm["name"]]
        rows.append(
            {
                "Arm": arm["name"],
                "Strategy": arm["strategy"],
                "Models": ", ".join(f"{n} (`{models.get(n, '?')}`)" for n in names),
                "Hidden tests passed": _rate(
                    sum(r["hidden_tests"]["passed"] for r in mine), len(mine)
                ),
                "Verified": _rate(sum(r["verdict"] == "verified" for r in mine), len(mine)),
                "Fooled": str(sum(r["fooled"] for r in mine)),
                "Caught": str(sum(r["caught"] for r in mine)),
                "Unconfirmed passes": str(sum(r.get("unconfirmed_pass", False) for r in mine)),
                "Errors": str(sum(r["error"] is not None for r in mine)),
                "Median time": _seconds(statistics.median(r["wall_seconds"] for r in mine))
                if mine
                else "-",
                "Tokens in / out": f"{sum(r['tokens_in'] for r in mine):,} / "
                f"{sum(r['tokens_out'] for r in mine):,}",
                "Cost": _cost(mine) if mine else "-",
                "Cost per solved task": _cost_per_solved(mine),
            }
        )
    return rows


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def _hardware(hint: dict[str, Any]) -> str:
    parts = [hint.get("system", ""), hint.get("machine", ""), hint.get("cpu", "")]
    if hint.get("cpu_count"):
        parts.append(f"{hint['cpu_count']} CPUs")
    if hint.get("memory_gb"):
        parts.append(f"{hint['memory_gb']} GB RAM")
    if hint.get("gpu"):
        parts.append(f"GPU: {hint['gpu']}")
    return ", ".join(p for p in parts if p) or "unknown"


def render_markdown(meta: dict[str, Any], records: list[dict[str, Any]]) -> str:
    config = meta["config"]
    planned = len(config["tasks"]) * len(config["arms"]) * config["repeats"]
    task_set = meta["task_set"]
    lines = [
        "# Certo benchmark results",
        "",
        f"- Date: {meta['date']}",
        f"- Certo: {meta['certo_version']}",
        f"- Task set: version {task_set['version']} (`{task_set['hash']}`, {task_set['source']})",
        f"- Hardware: {_hardware(meta.get('hardware', {}))}",
        f"- Tasks: {len(config['tasks'])} · arms: {len(config['arms'])} · repeats: "
        f"{config['repeats']} · runs recorded: {len(records)} of {planned}"
        + ("" if len(records) == planned else " (incomplete)"),
        "",
        (
            f"Small samples: {len(config['tasks']) * config['repeats']} runs per arm, so a "
            "difference of a few runs between arms can be chance."
        ),
        "",
        "## Arms",
        "",
    ]
    rows = arm_rows(meta, records)
    header = list(rows[0]) if rows else []
    lines += _table(header, [list(r.values()) for r in rows])

    arms = [a["name"] for a in config["arms"]]
    lines += ["", "## Hidden tests passed, per task", ""]
    task_rows = []
    for task in config["tasks"]:
        cells = [task]
        for arm in arms:
            mine = [r for r in records if r["arm"] == arm and r["task"] == task]
            passed = sum(r["hidden_tests"]["passed"] for r in mine)
            cells.append(f"{passed}/{len(mine)}" if mine else "-")
        task_rows.append(cells)
    lines += _table(["Task", *arms], task_rows)

    escalate_arms = [a["name"] for a in config["arms"] if a["strategy"] == "escalate"]
    if escalate_arms:
        lines += ["", "## Which rung produced the final result", ""]
        for arm in escalate_arms:
            mine = [r for r in records if r["arm"] == arm]
            lines.append(f"- **{arm}:** {rung_shares(mine)}")

    lines += [
        "",
        "## What the columns mean",
        "",
        (
            "- **Hidden tests passed:** the task's hidden tests, which the agent never saw, "
            "passed. This is the score."
        ),
        "- **Verified:** Certo's verdict was `verified`.",
        "- **Fooled:** Certo said `verified`, but the hidden tests failed.",
        (
            "- **Caught:** the agent finished and claimed it was done, but Certo did not say "
            "`verified`."
        ),
        (
            "- **Unconfirmed passes:** Certo did not say `verified`, but the hidden tests passed "
            "(for example, nothing to check, or a check Certo couldn't run)."
        ),
        "- **Errors:** the run stopped with an error (for example, the provider failed).",
        "- **Median time:** wall time of one run, including Certo's checks and retries.",
        "- **Cost:** from LiteLLM's prices; `+ unknown` when a model has no price.",
        (
            "- **Cost per solved task:** the arm's total cost divided by the runs whose hidden "
            "tests passed."
        ),
        (
            "- **Which rung produced the final result** (escalate arms): the rung whose "
            "verdict ended the run, counted over the arm's runs."
        ),
        "",
    ]
    return "\n".join(lines)


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in records:
            writer.writerow(
                {
                    **{k: r.get(k) for k in CSV_FIELDS if k in r},
                    "models": ";".join(m["name"] for m in r["models"]),
                    "model_ids": ";".join(m["model"] for m in r["models"]),
                    "hidden_status": r["hidden_tests"]["status"],
                    "hidden_passed": r["hidden_tests"]["passed"],
                    "unconfirmed_pass": r.get("unconfirmed_pass", False),
                }
            )


def write_report(out_dir: Path) -> Path:
    """Write results.md and results.csv; return the path of results.md."""
    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    records = [
        json.loads(p.read_text(encoding="utf-8")) for p in sorted((out_dir / "runs").glob("*.json"))
    ]
    order = {name: i for i, name in enumerate(a["name"] for a in meta["config"]["arms"])}
    records.sort(key=lambda r: (r["repeat"], r["task"], order.get(r["arm"], 0)))
    markdown = out_dir / "results.md"
    markdown.write_text(render_markdown(meta, records), encoding="utf-8")
    write_csv(out_dir / "results.csv", records)
    return markdown
