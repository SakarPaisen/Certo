"""Benchmark strategies: how one arm turns a task into a finished workspace.

A strategy is one entry in `STRATEGIES`. It knows which keys it reads from a
`bench.yaml` arm (`parse`), which `models.yaml` entries it uses (`models`),
and how to run one task in a prepared workspace (`run`). The bench runner
only uses this interface, so a later strategy, such as `cascade` (several
models in order) or `best_of` (N attempts, the verifier picks), is one new
class and one new entry here, with no change to the runner.

Models always come from the `models.yaml` catalog, by name, and reach the
normal Certo pipeline as an explicit configuration: never through `.env`.
No SDK import: the pipeline (`runner.stream_task`) is passed in by the
caller, so this module is testable with a fake.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from .config import DEFAULT_MAX_ITERATIONS, Config, override_llm
from .model_catalog import ModelCatalogEntry


class BenchConfigError(ValueError):
    """A bench.yaml problem. The message is user-facing."""


@dataclass(frozen=True)
class RunContext:
    """Everything a strategy needs to run one task once."""

    task_text: str
    workspace: str
    catalog: Mapping[str, ModelCatalogEntry]
    # An empty folder of its own: user skills, third-party skills and
    # projects are pointed here, so only Certo's built-in skills load and no
    # file outside the run can change it.
    isolation_dir: str
    # runner.stream_task, or a fake in tests.
    stream: Callable[..., Any]


@dataclass(frozen=True)
class AttemptResult:
    """What a strategy reports back: the fields of Certo's TaskOutcome the
    benchmark records, plus the catalog names it actually used."""

    verification_state: str
    retries_used: int
    run_summary: Any  # run_summary.RunSummary | None
    models_used: tuple[str, ...]


class Strategy(Protocol):
    name: str
    description: str

    def parse(
        self, arm: Mapping[str, Any], catalog: Mapping[str, ModelCatalogEntry], where: str
    ) -> dict[str, Any]: ...

    def models(self, params: Mapping[str, Any]) -> list[str]: ...

    def run(self, ctx: RunContext, params: Mapping[str, Any]) -> AttemptResult: ...


def run_config(entry: ModelCatalogEntry, workspace: str, isolation_dir: str) -> Config:
    """The Config for one run: Certo's defaults, the catalog entry's model
    settings, and nothing read from `.env` or the user settings file. An
    entry's empty field stays empty (a local model never inherits another
    provider's key), as with `--auto-model`'s catalog entries."""
    base = Config(
        model=entry.model,
        api_key=None,
        base_url=None,
        workspace=workspace,
        max_iterations=DEFAULT_MAX_ITERATIONS,
        confirm_mode="never",
        execution="local",
        projects_dir=os.path.join(isolation_dir, "projects"),
        skills_dir=os.path.join(isolation_dir, "skills"),
        third_party_skills_dir=os.path.join(isolation_dir, "third_party_skills"),
        third_party_skills_lock=os.path.join(isolation_dir, "third_party_skills.lock.json"),
        no_worktree_warning=True,
    )
    return override_llm(
        base,
        model=entry.model,
        api_key=entry.api_key or "",
        base_url=entry.base_url or "",
        reasoning_effort=entry.reasoning_effort or "",
    )


def model_name(
    arm: Mapping[str, Any], key: str, catalog: Mapping[str, ModelCatalogEntry], where: str
) -> str:
    """Read one catalog name from an arm, with an error that lists the
    names the catalog has."""
    value = arm.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BenchConfigError(f"{where}: '{key}' must be a model name from models.yaml.")
    if value not in catalog:
        names = ", ".join(sorted(catalog)) or "(none)"
        raise BenchConfigError(f"{where}: unknown model {value!r}. The models file has: {names}.")
    return value


def reject_unknown_keys(arm: Mapping[str, Any], allowed: set[str], where: str) -> None:
    extra = sorted(set(arm) - allowed - {"name", "strategy"})
    if extra:
        raise BenchConfigError(
            f"{where}: unknown key(s) {', '.join(extra)}. This strategy takes: "
            f"name, strategy, {', '.join(sorted(allowed))}."
        )


class SingleStrategy:
    """One model, the normal Certo run: exactly what `certo "<task>"` does."""

    name = "single"
    description = "one model, the normal Certo run"

    def parse(self, arm, catalog, where):
        reject_unknown_keys(arm, {"model"}, where)
        return {"model": model_name(arm, "model", catalog, where)}

    def models(self, params):
        return [params["model"]]

    def run(self, ctx, params):
        entry = ctx.catalog[params["model"]]
        cfg = run_config(entry, ctx.workspace, ctx.isolation_dir)
        outcome = ctx.stream(ctx.task_text, cfg=cfg)
        return AttemptResult(
            verification_state=outcome.verification_state,
            retries_used=outcome.retries_used,
            run_summary=outcome.run_summary,
            models_used=(entry.name,),
        )


# The registry. A new strategy is one more entry.
STRATEGIES: dict[str, Strategy] = {s.name: s for s in (SingleStrategy(),)}
