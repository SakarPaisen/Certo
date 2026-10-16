"""Escalation ladders: which models a task climbs through, and in what order.

A ladder is explicit (written under `escalation.ladders` in `models.yaml`)
or derived from the active models' ratings. Both resolve to a
`ResolvedLadder`, printed before a run and written to MODEL_DECISIONS.md.

Derived order, for one task:

- capability = the matched task profile's weighted sum over every axis
  except the cost axis (`escalation.cost_axis`, default `cost`), using the
  same classification as `--auto-model`;
- ascending capability; ties: higher cost rating first (a higher `cost`
  rating means cheaper), then the model name;
- at most `max_rungs` rungs: with n models and k rungs, rung j (0-based)
  is model number floor(j * (n - 1) / (k - 1) + 0.5), so the first rung is
  the least capable model, the last rung the most capable one, and the
  ones between are spread evenly.

Pure: no SDK, no network. The run loop lives in runner.py.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from .catalog_check import usable_rungs
from .model_catalog import (
    Ladder,
    LadderRung,
    ModelCatalog,
    ModelCatalogEntry,
    capability,
    classify_task,
)

# Final verdicts that mean "this model couldn't finish the job": the next
# rung gets the task. Never `inconclusive` (nothing to act on), and never
# `budget_exhausted` or `confirmation_required` (the user's own limits).
# `acceptance_failed` only when the ladder opts in.
ESCALATING_VERDICTS = ("retry_exhausted", "no_progress", "timed_out", "incomplete", "stuck")


class EscalationError(ValueError):
    """A request for escalation that can't be met. The message is user-facing."""


@dataclass(frozen=True)
class Rung:
    entry: ModelCatalogEntry
    retries: int | None  # None: CERTO_MAX_VERIFY_RETRIES
    reasoning_effort: str | None  # None: the entry's own
    capability: float
    cost_rating: float | None

    @property
    def name(self) -> str:
        return self.entry.name


@dataclass(frozen=True)
class ResolvedLadder:
    kind: str  # "explicit" | "derived"
    name: str | None  # the ladder's name; None when derived
    rungs: tuple[Rung, ...]
    task_profile: str
    weights: dict[str, float]
    cost_axis: str
    escalate_on_acceptance_failed: bool = False
    # Plain-language notes on rungs left out (inactive models).
    skipped: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        if self.kind == "derived":
            return f"derived ladder (task profile '{self.task_profile}')"
        return f"explicit ladder '{self.name}'"

    def escalates_on(self, verdict: str) -> bool:
        if verdict in ESCALATING_VERDICTS:
            return True
        return verdict == "acceptance_failed" and self.escalate_on_acceptance_failed


def spread_indices(n: int, k: int) -> list[int]:
    """Which of n ordered models a k-rung ladder keeps: all of them when
    n <= k, else the first, the last, and evenly spread ones between."""
    if n <= k:
        return list(range(n))
    return [math.floor(j * (n - 1) / (k - 1) + 0.5) for j in range(k)]


def _rung(entry: ModelCatalogEntry, weights, cost_axis, retries=None, effort=None) -> Rung:
    return Rung(
        entry=entry,
        retries=retries,
        reasoning_effort=effort,
        capability=capability(entry, weights, cost_axis),
        cost_rating=entry.ratings.get(cost_axis),
    )


def derive_ladder(catalog: ModelCatalog, task: str) -> ResolvedLadder:
    settings = catalog.escalation
    profile = classify_task(task, catalog)
    active = [m for m in catalog.models if m.activated]
    if not active:
        raise EscalationError("Every model has 'activated: false', so there is nothing to climb.")
    scored = [_rung(m, profile.weights, settings.cost_axis) for m in active]
    scored.sort(key=lambda r: (r.capability, -(r.cost_rating or 0.0), r.name))
    chosen = tuple(scored[i] for i in spread_indices(len(scored), settings.max_rungs))
    return ResolvedLadder(
        kind="derived",
        name=None,
        rungs=chosen,
        task_profile=profile.name,
        weights=dict(profile.weights),
        cost_axis=settings.cost_axis,
    )


def explicit_ladder(catalog: ModelCatalog, ladder: Ladder, task: str) -> ResolvedLadder:
    settings = catalog.escalation
    profile = classify_task(task, catalog)
    by_name = {m.name: m for m in catalog.models}
    usable = usable_rungs(ladder, catalog)
    skipped = tuple(
        f"{r.model} (activated: false)"
        for r in ladder.rungs
        if r.model in by_name and not by_name[r.model].activated
    )
    if not usable:
        raise EscalationError(
            f"Ladder '{ladder.name}' has no usable rung: every model in it is missing or "
            "has 'activated: false'."
        )
    rungs = tuple(
        _rung(by_name[r.model], profile.weights, settings.cost_axis, r.retries, r.reasoning_effort)
        for r in usable
    )
    return ResolvedLadder(
        kind="explicit",
        name=ladder.name,
        rungs=rungs,
        task_profile=profile.name,
        weights=dict(profile.weights),
        cost_axis=settings.cost_axis,
        escalate_on_acceptance_failed=ladder.escalate_on_acceptance_failed,
        skipped=skipped,
    )


def ladder_from_models(
    catalog: ModelCatalog, names: Sequence[str], task: str, *, name: str = "models"
) -> ResolvedLadder:
    """An explicit ladder from a list of model names (`certo bench` arms)."""
    ladder = Ladder(name=name, rungs=tuple(LadderRung(model=n) for n in names))
    return explicit_ladder(catalog, ladder, task)


def resolve_ladder(catalog: ModelCatalog, task: str, name: str | None) -> ResolvedLadder:
    """The ladder `--escalate [NAME]` uses: the named one; with no name, the
    ladder called `default` when it exists, else a derived one."""
    ladders = catalog.escalation.ladders
    if name:
        if name not in ladders:
            known = ", ".join(sorted(ladders)) or "none (only a derived ladder is available)"
            raise EscalationError(
                f"There is no escalation ladder named '{name}' in models.yaml. Ladders: {known}."
            )
        return explicit_ladder(catalog, ladders[name], task)
    if "default" in ladders:
        return explicit_ladder(catalog, ladders["default"], task)
    return derive_ladder(catalog, task)


def describe_rung(rung: Rung, *, scores: bool) -> str:
    extra = []
    if scores:
        cost = "unrated" if rung.cost_rating is None else f"{rung.cost_rating:g}"
        extra.append(f"capability {rung.capability:g}, cost rating {cost}")
    if rung.retries is not None:
        extra.append(f"{rung.retries} fix attempt(s)")
    if rung.reasoning_effort:
        extra.append(f"reasoning {rung.reasoning_effort}")
    return rung.name + (f" ({'; '.join(extra)})" if extra else "")


def describe_ladder(ladder: ResolvedLadder) -> list[str]:
    """The lines printed before an escalation run starts."""
    lines = [f"Escalation: {ladder.label}, {len(ladder.rungs)} rung(s):"]
    for i, rung in enumerate(ladder.rungs, start=1):
        lines.append(f"  {i}. {describe_rung(rung, scores=ladder.kind == 'derived')}")
    if ladder.skipped:
        lines.append(f"  Skipped: {', '.join(ladder.skipped)}")
    if len(ladder.rungs) == 1:
        lines.append("  Only one rung: this task can't escalate.")
    return lines
