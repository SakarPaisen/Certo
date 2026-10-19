"""Where Certo finds its model files.

`models_list.yaml` is the catalog (model ids, descriptions, ratings);
`models.yaml` holds the user's personal settings (which models to use,
keys, addresses, overrides). Two more are optional, one per mode:
`task_profiles.yaml` (`--auto-model`) and `escalation.yaml` (`--escalate`,
and `certo bench`). Certo ships all four only as examples, in
`certo/examples/`, and never reads an example: a release can update the
examples without touching anyone's own copies.

Each file is looked up on its own: the path a setting names
(`CERTO_MODELS_LIST_FILE`, `CERTO_MODELS_FILE`, `CERTO_TASK_PROFILES_FILE`,
`CERTO_ESCALATION_FILE`, or a benchmark file's keys), else the current
folder, else the user settings folder (next to the user `.env`,
`~/.config/certo/`). The first one found is used whole.
"""

from __future__ import annotations

import os
from pathlib import Path

from .config import user_settings_path
from .model_catalog import (
    ESCALATION_FILE,
    LIST_FILE,
    MODELS_FILE,
    PROFILES_FILE,
    ModelCatalogError,
)

EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"


def user_dir() -> str:
    return os.path.dirname(user_settings_path())


def example_path(name: str) -> str:
    return str(EXAMPLES_DIR / f"{name}.example")


def _search_folders() -> tuple[str, ...]:
    return (os.getcwd(), user_dir())


def find(name: str, explicit: str = "") -> str | None:
    """The file to use for `name`, or None when there is none. An explicit
    path is returned as is, even if missing, so the error can name it."""
    if explicit:
        return explicit
    for folder in _search_folders():
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            return path
    return None


def missing_message(name: str, setting: str) -> str:
    return (
        f"No {name} found: Certo looked in the current folder and in {user_dir()}. "
        f"Certo ships an example to start from; copy it and edit it:\n"
        f"  cp {example_path(name)} {os.path.join(user_dir(), name)}\n"
        f"(or put it in the project folder, or set {setting})."
    )


def resolve(models_file: str = "", models_list_file: str = "") -> tuple[str, str]:
    """(models_list.yaml, models.yaml) paths. Raises `ModelCatalogError`
    saying how to create a missing one, or naming an explicit path that
    doesn't exist."""
    paths = []
    for name, explicit, setting in (
        (LIST_FILE, models_list_file, "CERTO_MODELS_LIST_FILE"),
        (MODELS_FILE, models_file, "CERTO_MODELS_FILE"),
    ):
        path = find(name, explicit)
        if path is None:
            raise ModelCatalogError(missing_message(name, setting))
        if not os.path.isfile(path):
            raise ModelCatalogError(f"{setting} names {path}, which doesn't exist.")
        paths.append(path)
    return paths[0], paths[1]


def resolve_optional(
    task_profiles_file: str = "", escalation_file: str = ""
) -> tuple[str | None, str | None]:
    """(task_profiles.yaml, escalation.yaml) paths, None for one that isn't
    there: both are optional. A path a setting names must exist."""
    paths: list[str | None] = []
    for name, explicit, setting in (
        (PROFILES_FILE, task_profiles_file, "CERTO_TASK_PROFILES_FILE"),
        (ESCALATION_FILE, escalation_file, "CERTO_ESCALATION_FILE"),
    ):
        path = find(name, explicit)
        if path is not None and not os.path.isfile(path):
            raise ModelCatalogError(f"{setting} names {path}, which doesn't exist.")
        paths.append(path)
    return paths[0], paths[1]
