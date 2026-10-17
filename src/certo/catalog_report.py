"""The model catalog part of `certo check`: what `models.yaml` holds, the
ladders it gives, its problems, and (with `--models`) a real tool-call test
of every active model. Never prints a key."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TextIO

from .catalog_check import check_catalog, usable_rungs
from .config import DEFAULT_MAX_ITERATIONS, Config
from .escalation import EscalationError, derive_ladder, describe_rung
from .model_catalog import (
    LIST_FILE,
    MODELS_FILE,
    ModelCatalog,
    ModelCatalogEntry,
    ModelCatalogError,
    load_model_catalog,
)
from .model_files import find, missing_message, resolve
from .model_selection import config_for_entry

# llm_check.explain() names the .env settings; for a catalog entry the fix
# is in its models.yaml fields instead.
_FIELD_NAMES = {
    "CERTO_LLM_API_KEY in .env": "its api_key in models.yaml",
    "CERTO_LLM_MODEL in .env": "its model id in models_list.yaml",
    "CERTO_LLM_BASE_URL in .env": "its base_url in models.yaml",
}


def _setting(name: str) -> str:
    return (os.environ.get(f"CERTO_{name}") or os.environ.get(f"HARNESS_{name}") or "").strip()


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
    inactive = [m.name for m in catalog.models if m.configured and not m.activated]
    unlisted = sum(not m.configured for m in catalog.models)
    lines = [f"  Active models: {', '.join(active) or 'none'}"]
    if inactive:
        lines.append(f"  Inactive models: {', '.join(inactive)}")
    if unlisted:
        lines.append(
            f"  {unlisted} other model(s) in models_list.yaml, not used (not in models.yaml)"
        )
    for ladder in catalog.escalation.ladders.values():
        usable = usable_rungs(ladder, catalog)
        rungs = " -> ".join(r.model for r in usable) or "no usable rung"
        skipped = len(ladder.rungs) - len(usable)
        note = f" ({skipped} rung(s) skipped)" if skipped else ""
        lines.append(f"  Ladder '{ladder.name}': {rungs}{note}")
    try:
        derived = derive_ladder(catalog)
    except EscalationError:
        lines.append("  Derived ladder: none (no active model)")
    else:
        rungs = " -> ".join(describe_rung(r, scores=True) for r in derived.rungs)
        lines.append(f"  Derived ladder: {rungs}")
    return lines


def print_catalog_report(
    out: TextIO,
    *,
    test_models: bool,
    timeout: int,
    check: Callable,
    explain: Callable,
) -> bool:
    """Print the catalog report; return False on any error or failed test.

    `check`/`explain` are llm_check's `check_tool_calling`/`explain`, passed
    in so tests can fake the model call."""
    models_file, list_file = _setting("MODELS_FILE"), _setting("MODELS_LIST_FILE")
    found = (find(LIST_FILE, list_file), find(MODELS_FILE, models_file))
    if found == (None, None):
        if test_models:
            print(f"--models: {missing_message(MODELS_FILE, 'CERTO_MODELS_FILE')}", file=out)
            return False
        return True
    print("Model files:", file=out)
    try:
        list_path, models_path = resolve(models_file, list_file)
        print(f"  List: {list_path}", file=out)
        print(f"  Personal settings: {models_path}", file=out)
        catalog = load_model_catalog(list_path, models_path, strict=False)
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
