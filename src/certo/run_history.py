"""`.certo/RUNS.md` in a project: one entry per `certo` run, never deleted.

`STATUS.md` (project_state.py) holds only the last run, so it can't answer
"which model built this?" a few runs later. This file can: each entry has
the date, the Certo version, the model (or every rung of an escalation),
the verdict, the time and the cost. Written by Certo after the run, never
by the agent; model names only, never a key. Stdlib only.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from . import __version__
from .project_state import ensure_state_dir, state_dir
from .run_summary import RunSummary, format_duration

RUNS_FILE = "RUNS.md"

_HEADER = (
    "# Certo runs in this folder\n"
    "\n"
    "One entry per `certo` run, oldest first. Written by Certo, never by the\n"
    "agent. Model names only, never keys.\n"
)


@dataclass(frozen=True)
class RunEntry:
    task: str
    ended: str  # a verdict, or "interrupted", or "error: ..."
    started_at: datetime
    # What ran: one line per model or rung, e.g. "openai/gpt-5.6-luna" or
    # "1. local (ollama/qwen3.8:27b): unchanged, ...".
    models: Sequence[str]
    summary: RunSummary | None = None
    resumed: bool = False
    note: str = ""  # e.g. how the model was chosen


def runs_path(workspace: str) -> str:
    return os.path.join(state_dir(workspace), RUNS_FILE)


def _first_line(text: str, limit: int = 100) -> str:
    line = text.strip().splitlines()[0] if text.strip() else ""
    return line if len(line) <= limit else line[: limit - 1] + "…"


def render_entry(entry: RunEntry) -> str:
    when = entry.started_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"## {when} · {entry.ended}", ""]
    task = _first_line(entry.task) or "(no task text)"
    lines.append(f"- Task: {task}" + (" (resumed)" if entry.resumed else ""))
    lines.append(f"- Certo: {__version__}")
    if len(entry.models) == 1:
        lines.append(f"- Model: {entry.models[0]}" + (f" ({entry.note})" if entry.note else ""))
    elif entry.models:
        lines.append("- Models:" + (f" {entry.note}" if entry.note else ""))
        lines += [f"  - {m}" for m in entry.models]
    if entry.summary is not None:
        s = entry.summary
        cost = f"${s.total_cost:.4f}" + ("" if s.cost_complete else " + unknown")
        lines.append(
            f"- Time: {format_duration(s.duration_seconds)} · "
            f"Tokens: {s.total_tokens:,} · Cost: {cost}"
        )
    return "\n".join(lines) + "\n"


def append_run(workspace: str, entry: RunEntry) -> None:
    """Add one entry, creating `.certo/` and the file when needed. Raises
    OSError; the caller decides that a failed write never fails the run."""
    ensure_state_dir(workspace)
    path = runs_path(workspace)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(_HEADER)
        f.write("\n" + render_entry(entry))
