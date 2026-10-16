"""The model catalog part of `certo check`: what `models.yaml` holds, the
ladders it gives, its problems, and (with `--models`) a real tool-call test
of every active model. Never prints a key."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TextIO

from .catalog_check import check_catalog, usable_rungs
from .config import DEFAULT_MAX_ITERATIONS, DEFAULT_MODELS_FILE, Config
from .escalation import EscalationError, derive_ladder, describe_rung
from .model_catalog import ModelCatalog, ModelCatalogEntry, ModelCatalogError, load_model_catalog
from .model_selection import config_for_entry

# llm_check.explain() names the .env settings; for a catalog entry the fix
# is in its models.yaml fields instead.
_FIELD_NAMES = {
    "CERTO_LLM_API_KEY in .env": "its api_key in models.yaml",
    "CERTO_LLM_MODEL in .env": "its model in models.yaml",
    "CERTO_LLM_BASE_URL in .env": "its base_url in models.yaml",
}


def models_file() -> str:
    """The catalog `--auto-model` and `--escalate` read."""
    return (
        os.environ.get("CERTO_MODELS_FILE") or os.environ.get("HARNESS_MODELS_FILE") or ""
    ).strip() or DEFAULT_MODELS_FILE


def entry_config(entry: ModelCatalogEntry) -> Config:
    """A Config with only this entry's model settings: nothing from .env."""
    base = Config(
        model=entry.model,
        api_key=None,
        base_url=None,
        workspace=".",
        max_iterations=DEFAULT_MAX_ITERATIONS,
        confirm_mode="never",
        execution="local",
    )
    return config_for_entry(base, entry)


def _catalog_lines(catalog: ModelCatalog) -> list[str]:
    active = [m.name for m in catalog.models if m.activated]
    inactive = [m.name for m in catalog.models if not m.activated]
    lines = [f"  Active models: {', '.join(active) or 'none'}"]
    if inactive:
        lines.append(f"  Inactive models: {', '.join(inactive)}")
    for ladder in catalog.escalation.ladders.values():
        usable = usable_rungs(ladder, catalog)
        rungs = " -> ".join(r.model for r in usable) or "no usable rung"
        skipped = len(ladder.rungs) - len(usable)
        note = f" ({skipped} rung(s) skipped)" if skipped else ""
        lines.append(f"  Ladder '{ladder.name}': {rungs}{note}")
    try:
        derived = derive_ladder(catalog, "")
    except EscalationError:
        lines.append("  Derived ladder: none (no active model)")
    else:
        rungs = " -> ".join(describe_rung(r, scores=True) for r in derived.rungs)
        lines.append(f"  Derived ladder (task profile '{derived.task_profile}'): {rungs}")
    return lines


def print_catalog_report(
    out: TextIO,
    *,
    test_models: bool,
    timeout: int,
    check: Callable,
    explain: Callable,
    path: str | None = None,
) -> bool:
    """Print the catalog report; return False on any error or failed test.

    `check`/`explain` are llm_check's `check_tool_calling`/`explain`, passed
    in so tests can fake the model call."""
    path = path or models_file()
    if not os.path.isfile(path):
        if test_models:
            print(
                f"--models: there is no model catalog at {path}. Copy models.yaml.example "
                "to models.yaml (or set CERTO_MODELS_FILE).",
                file=out,
            )
            return False
        return True
    print(f"Model catalog: {path}", file=out)
    try:
        catalog = load_model_catalog(path, strict=False)
    except ModelCatalogError as exc:
        print(f"  Error: {exc}", file=out)
        print(file=out)
        return False
    report = check_catalog(catalog)
    for line in _catalog_lines(catalog):
        print(line, file=out)
    for error in report.errors:
        print(f"  Error: {error}", file=out)
    for warning in report.warnings:
        print(f"  Warning: {warning}", file=out)
    ok = report.ok
    if test_models:
        active = [m for m in catalog.models if m.activated]
        print("Checking every active model:", file=out)
        for entry in active:
            print(f"  {entry.name} ({entry.model})...", end=" ", file=out, flush=True)
            result = check(entry_config(entry), timeout=timeout)
            text = explain(result, None)
            for old, new in _FIELD_NAMES.items():
                text = text.replace(old, new)
            print(text, file=out)
            ok = ok and result.ok
    print(file=out)
    return ok
