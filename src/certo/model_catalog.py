"""Pure data model, parsing, and scoring for `CERTO_MODEL_SELECTION=auto`'s
model catalog (`models.yaml`) — no SDK imports, no side effects beyond
reading the one file, fully unit-testable without a `Conversation`.

`models.yaml` is git-ignored (see `.gitignore`) because real API keys live
directly in it — same treatment as `.env`. `models.yaml.example` is the
checked-in template. See MANUAL.md "Automatic model selection" for the
user-facing writeup and ROADMAP.md's decisions log for the design history
(deterministic weighted scoring was chosen over an LLM-based router; one
static ranked list per task, not re-scored mid-task; no hard minimum catalog
size — see `rank_candidates`).

Rating/weight axes are deliberately open-ended, not hardcoded to a fixed set
(`reasoning`/`cost`/`precision`/`code` are just the template's example) —
scoring iterates whatever keys a task profile's `weights` declares, so a
user can add a new axis with zero code changes.

Each model entry also has `activated` (bool, default `true`) — a
deactivated entry stays in the file (still schema-validated, still counted
for duplicate-name checks) but is excluded from `rank_candidates()`'s
scoring/output entirely, letting a user maintain a large catalog and
toggle individual models on/off without deleting or re-adding entries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .config import DEFAULT_LLM_TIMEOUT_SECONDS


class ModelCatalogError(ValueError):
    """Raised when `models.yaml` is missing, malformed, or fails schema
    validation. Message is user-facing."""


@dataclass(frozen=True)
class ModelCatalogEntry:
    """One candidate model. `api_key`/`base_url`/`reasoning_effort` mirror
    the exact same fields `.env`'s CERTO_LLM_API_KEY/CERTO_LLM_BASE_URL/
    CERTO_LLM_REASONING_EFFORT carry for the single-model default — see
    `model_selection.py`'s `llm_for_entry()`, which builds an actual `LLM`
    from one of these via `config.override_llm()`, not a separate builder.
    """

    name: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
    reasoning_effort: str | None = None
    # How long one call to this model may take; 0 = no limit. Not inherited
    # from CERTO_LLM_TIMEOUT_SECONDS: an entry is a complete model spec.
    timeout_seconds: int = DEFAULT_LLM_TIMEOUT_SECONDS
    description: str = ""
    ratings: dict[str, float] = field(default_factory=dict)
    activated: bool = True


@dataclass(frozen=True)
class TaskProfile:
    """A named weight vector, selected by keyword match against the task
    text — same `KeywordTrigger`-style deterministic matching this project's
    skills already use, not an LLM classification call."""

    name: str
    triggers: tuple[str, ...] = ()
    weights: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class LadderRung:
    """One step of an explicit escalation ladder: a catalog model by name,
    optionally with its own fix-attempt budget and reasoning effort."""

    model: str
    retries: int | None = None  # None: CERTO_MAX_VERIFY_RETRIES
    reasoning_effort: str | None = None  # None: the model entry's own


@dataclass(frozen=True)
class Ladder:
    name: str
    rungs: tuple[LadderRung, ...]
    escalate_on_acceptance_failed: bool = False


DEFAULT_COST_AXIS = "cost"
DEFAULT_MAX_RUNGS = 3


@dataclass(frozen=True)
class EscalationSettings:
    """The optional top-level `escalation:` section (see escalation.py)."""

    cost_axis: str = DEFAULT_COST_AXIS
    # Whether `cost_axis` was written in the file: only then is an axis no
    # model is rated on an error (catalog_check.py).
    cost_axis_set: bool = False
    max_rungs: int = DEFAULT_MAX_RUNGS
    ladders: dict[str, Ladder] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelCatalog:
    models: list[ModelCatalogEntry]
    task_profiles: list[TaskProfile]
    escalation: EscalationSettings = field(default_factory=EscalationSettings)


_DEFAULT_PROFILE = TaskProfile(name="default", triggers=(), weights={})


def _require_str(data: dict, key: str, *, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ModelCatalogError(f"{context}: {key!r} must be a non-empty string.")
    return value


def _optional_str(data: dict, key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ModelCatalogError(f"{key!r} must be a string if given.")
    value = value.strip()
    return value or None


def _parse_ratings(data: dict, *, context: str) -> dict[str, float]:
    raw = data.get("ratings", {}) or {}
    if not isinstance(raw, dict):
        raise ModelCatalogError(f"{context}: 'ratings' must be a mapping of axis -> number.")
    ratings: dict[str, float] = {}
    for axis, value in raw.items():
        try:
            ratings[str(axis)] = float(value)
        except (TypeError, ValueError):
            raise ModelCatalogError(
                f"{context}: rating {axis!r} must be a number, got {value!r}."
            ) from None
    return ratings


def _parse_timeout(data: dict, *, context: str) -> int:
    if data.get("timeout_seconds") is None:
        return DEFAULT_LLM_TIMEOUT_SECONDS
    value = data["timeout_seconds"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ModelCatalogError(
            f"{context}: 'timeout_seconds' must be zero or a positive whole number "
            f"of seconds, got {value!r}."
        )
    return value


def _parse_activated(data: dict, *, context: str) -> bool:
    if "activated" not in data:
        return True
    value = data["activated"]
    if not isinstance(value, bool):
        raise ModelCatalogError(f"{context}: 'activated' must be true or false, got {value!r}.")
    return value


def _parse_model_entry(data: Any) -> ModelCatalogEntry:
    if not isinstance(data, dict):
        raise ModelCatalogError("Each entry under 'models' must be a mapping.")
    name = _require_str(data, "name", context="A model entry")
    context = f"Model {name!r}"
    model = _require_str(data, "model", context=context)
    return ModelCatalogEntry(
        name=name,
        model=model,
        api_key=_optional_str(data, "api_key"),
        base_url=_optional_str(data, "base_url"),
        reasoning_effort=_optional_str(data, "reasoning_effort"),
        timeout_seconds=_parse_timeout(data, context=context),
        description=(_optional_str(data, "description") or ""),
        ratings=_parse_ratings(data, context=context),
        activated=_parse_activated(data, context=context),
    )


def _parse_weights(data: dict, *, context: str) -> dict[str, float]:
    raw = data.get("weights", {}) or {}
    if not isinstance(raw, dict):
        raise ModelCatalogError(f"{context}: 'weights' must be a mapping of axis -> number.")
    weights: dict[str, float] = {}
    for axis, value in raw.items():
        try:
            weights[str(axis)] = float(value)
        except (TypeError, ValueError):
            raise ModelCatalogError(
                f"{context}: weight {axis!r} must be a number, got {value!r}."
            ) from None
    return weights


def _parse_task_profile(name: str, data: Any) -> TaskProfile:
    if not isinstance(data, dict):
        raise ModelCatalogError(f"Task profile {name!r} must be a mapping.")
    triggers_raw = data.get("triggers", []) or []
    if not isinstance(triggers_raw, list) or not all(isinstance(t, str) for t in triggers_raw):
        raise ModelCatalogError(f"Task profile {name!r}: 'triggers' must be a list of strings.")
    return TaskProfile(
        name=name,
        triggers=tuple(triggers_raw),
        weights=_parse_weights(data, context=f"Task profile {name!r}"),
    )


_ESCALATION_KEYS = {"cost_axis", "max_rungs", "ladders"}
_LADDER_KEYS = {"rungs", "escalate_on_acceptance_failed"}
_RUNG_KEYS = {"model", "retries", "reasoning_effort"}


def _parse_rung(data: Any, *, context: str) -> LadderRung:
    if not isinstance(data, dict):
        raise ModelCatalogError(f"{context}: each rung must be a mapping with a 'model' name.")
    unknown = sorted(set(data) - _RUNG_KEYS)
    if unknown:
        raise ModelCatalogError(
            f"{context}: unknown key(s) {', '.join(unknown)}. "
            f"A rung takes: {', '.join(sorted(_RUNG_KEYS))}."
        )
    model = _require_str(data, "model", context=context)
    retries = data.get("retries")
    if retries is not None and (isinstance(retries, bool) or not isinstance(retries, int)):
        raise ModelCatalogError(f"{context}: 'retries' must be a whole number, got {retries!r}.")
    return LadderRung(
        model=model.strip(),
        retries=retries,
        reasoning_effort=_optional_str(data, "reasoning_effort"),
    )


def _parse_ladder(name: str, data: Any) -> Ladder:
    """A ladder is a list of rungs, or a mapping with `rungs` and options."""
    context = f"Escalation ladder {name!r}"
    options: dict[str, Any] = {}
    if isinstance(data, dict):
        unknown = sorted(set(data) - _LADDER_KEYS)
        if unknown:
            raise ModelCatalogError(
                f"{context}: unknown key(s) {', '.join(unknown)}. "
                f"A ladder written as a mapping takes: {', '.join(sorted(_LADDER_KEYS))}."
            )
        options = data
        data = data.get("rungs")
    if not isinstance(data, list):
        raise ModelCatalogError(f"{context} must be a list of rungs.")
    on_acceptance = options.get("escalate_on_acceptance_failed", False)
    if not isinstance(on_acceptance, bool):
        raise ModelCatalogError(
            f"{context}: 'escalate_on_acceptance_failed' must be true or false."
        )
    rungs = tuple(
        _parse_rung(rung, context=f"{context}, rung {i}") for i, rung in enumerate(data, start=1)
    )
    return Ladder(name=name, rungs=rungs, escalate_on_acceptance_failed=on_acceptance)


def _parse_escalation(raw: Any, path: str) -> EscalationSettings:
    if raw is None:
        return EscalationSettings()
    if not isinstance(raw, dict):
        raise ModelCatalogError(f"{path}: 'escalation' must be a mapping.")
    unknown = sorted(set(raw) - _ESCALATION_KEYS)
    if unknown:
        raise ModelCatalogError(
            f"{path}: unknown key(s) under 'escalation': {', '.join(unknown)}. "
            f"Allowed: {', '.join(sorted(_ESCALATION_KEYS))}."
        )
    cost_axis = raw.get("cost_axis")
    if cost_axis is not None and (not isinstance(cost_axis, str) or not cost_axis.strip()):
        raise ModelCatalogError(f"{path}: 'escalation.cost_axis' must be a rating axis name.")
    max_rungs = raw.get("max_rungs", DEFAULT_MAX_RUNGS)
    if isinstance(max_rungs, bool) or not isinstance(max_rungs, int) or max_rungs < 2:
        raise ModelCatalogError(
            f"{path}: 'escalation.max_rungs' must be a whole number of at least 2, "
            f"got {max_rungs!r}."
        )
    ladders_raw = raw.get("ladders") or {}
    if not isinstance(ladders_raw, dict):
        raise ModelCatalogError(f"{path}: 'escalation.ladders' must be a mapping of name -> rungs.")
    return EscalationSettings(
        cost_axis=cost_axis.strip() if cost_axis else DEFAULT_COST_AXIS,
        cost_axis_set=cost_axis is not None,
        max_rungs=max_rungs,
        ladders={str(name): _parse_ladder(str(name), data) for name, data in ladders_raw.items()},
    )


def load_model_catalog(path: str, *, strict: bool = True) -> ModelCatalog:
    """Parse `models.yaml`. Raises `ModelCatalogError` for a missing file, a
    file that isn't valid YAML, or one that fails schema validation (a
    non-empty 'models' list, each with 'name'/'model'; 'activated' defaults
    to `true` if omitted; profiles are optional). No minimum catalog size is
    enforced — see `rank_candidates()`'s docstring for why (and for what
    happens when every model is deactivated).

    `strict=False` skips the duplicate-name check, so `catalog_check.py`
    can report it together with every other problem. Commands load the file
    through `catalog_check.load_checked_catalog`, which checks everything."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ModelCatalogError(
            f"CERTO_MODEL_SELECTION=auto requires a model catalog at {path!r}, "
            "but no such file exists. Copy models.yaml.example to models.yaml "
            "and fill in your models."
        )
    try:
        raw = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ModelCatalogError(f"{path} is not valid YAML: {exc}") from exc

    if not isinstance(raw, dict):
        raise ModelCatalogError(f"{path} must contain a mapping at the top level.")

    models_raw = raw.get("models")
    if not isinstance(models_raw, list) or not models_raw:
        raise ModelCatalogError(f"{path} must define a non-empty 'models' list.")
    models = [_parse_model_entry(entry) for entry in models_raw]

    seen_names = set()
    for entry in models:
        if strict and entry.name in seen_names:
            raise ModelCatalogError(f"{path}: duplicate model name {entry.name!r}.")
        seen_names.add(entry.name)

    profiles_raw = raw.get("task_profiles", {}) or {}
    if not isinstance(profiles_raw, dict):
        raise ModelCatalogError(f"{path}: 'task_profiles' must be a mapping of name -> profile.")
    task_profiles = [_parse_task_profile(name, data) for name, data in profiles_raw.items()]

    return ModelCatalog(
        models=models,
        task_profiles=task_profiles,
        escalation=_parse_escalation(raw.get("escalation"), path),
    )


def classify_task(task_text: str, catalog: ModelCatalog) -> TaskProfile:
    """First declared task profile whose trigger appears (case-insensitive
    substring match) in `task_text` wins — same tie-break convention as
    `_LANGUAGE_MARKERS` in `run_tests_tool.py`. Falls back to a profile named
    `default` if one is declared, else a synthesized empty-weights profile
    (every model scores 0 and the declared order breaks the tie — see
    `rank_candidates`).
    """
    lowered = task_text.lower()
    for profile in catalog.task_profiles:
        if profile.name == "default":
            continue
        if any(trigger.lower() in lowered for trigger in profile.triggers):
            return profile
    for profile in catalog.task_profiles:
        if profile.name == "default":
            return profile
    return _DEFAULT_PROFILE


def score_entry(entry: ModelCatalogEntry, weights: dict[str, float]) -> float:
    """Weighted sum over whatever axes `weights` declares — an axis a model
    doesn't rate itself on contributes 0, not an error."""
    return sum(entry.ratings.get(axis, 0.0) * weight for axis, weight in weights.items())


def capability(entry: ModelCatalogEntry, cost_axis: str) -> float:
    """How capable a model is, for escalation: the plain sum of its ratings
    on every axis except the cost axis. With the usual axes that is
    reasoning + precision + code. Task profiles don't change it: a ladder
    climbs by general capability, the same for every task."""
    return sum(value for axis, value in entry.ratings.items() if axis != cost_axis)


def rank_candidates(catalog: ModelCatalog, weights: dict[str, float]) -> list[ModelCatalogEntry]:
    """Every *activated* catalog model, scored against `weights` and sorted
    descending (stable — ties keep the file's declared order, via Python's
    stable sort over the already-declaration-ordered `catalog.models`).

    A model with `activated: false` is skipped entirely — not scored, not
    returned, never a fallback candidate — so a user can keep a large
    catalog on file and toggle individual models on/off without deleting or
    re-adding entries.

    No minimum length is enforced beyond "at least one activated model": a
    1- or 2-model catalog just produces a correspondingly short fallback
    chain, never an error for the model *count* — a user is free to add more
    models later without hitting a hidden validation cliff. Raises
    `ModelCatalogError` only if every model in the catalog is deactivated,
    since that leaves nothing to select from at all.
    """
    active = [entry for entry in catalog.models if entry.activated]
    if not active:
        raise ModelCatalogError(
            "Every model in the catalog has 'activated: false' — set at "
            "least one to 'true' before using CERTO_MODEL_SELECTION=auto."
        )
    return sorted(active, key=lambda entry: score_entry(entry, weights), reverse=True)
