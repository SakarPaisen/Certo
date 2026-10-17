"""Test helper: write the two model files from one combined text."""

from __future__ import annotations

import os


def write_model_files(folder, combined: str) -> tuple[str, str]:
    """Write a catalog given in one YAML text (the shape most tests read
    best: models with their keys, task_profiles, escalation) as the two real
    files, models_list.yaml and models.yaml, the way a user would split it:
    every model goes into models.yaml with its api_key, base_url and
    activated; the rest stays in the list. Returns (list path, models path)."""
    import yaml

    data = yaml.safe_load(combined)
    listed, personal = [], []
    for model in data.get("models") or []:
        model = dict(model)
        entry = {"name": model.get("name")}
        for key in ("api_key", "base_url", "activated"):
            if key in model:
                entry[key] = model.pop(key)
        listed.append(model)
        personal.append(entry)
    data["models"] = listed
    list_path = os.path.join(str(folder), "models_list.yaml")
    models_path = os.path.join(str(folder), "models.yaml")
    with open(list_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    with open(models_path, "w", encoding="utf-8") as f:
        yaml.safe_dump({"models": personal}, f, sort_keys=False)
    return list_path, models_path

