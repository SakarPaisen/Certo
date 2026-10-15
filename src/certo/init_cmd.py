"""`certo init [FOLDER]`: a ready-to-use workspace in one command.

Writes a minimal `.env`, a `.gitignore`, the sample tasks and a short
README into FOLDER. The provider presets and default models live in
`starter/providers.toml`, the only place they are kept.
"""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from dataclasses import dataclass
from importlib import resources
from typing import TextIO

DEFAULT_FOLDER = "certo-workspace"
README_TITLE = "# Certo workspace"

_STARTER = resources.files("certo").joinpath("starter")


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    model: str | None = None
    key_env: str | None = None
    key_url: str | None = None
    base_url: str | None = None
    small_model: str | None = None


def load_providers() -> list[Provider]:
    data = tomllib.loads(_STARTER.joinpath("providers.toml").read_text(encoding="utf-8"))
    fields = Provider.__dataclass_fields__
    return [Provider(**{k: v for k, v in p.items() if k in fields}) for p in data["provider"]]


def _preset_lines(provider: Provider) -> list[str]:
    """The two commented-out lines that select `provider`."""
    if provider.model is None:
        return []
    second = (
        f"# CERTO_LLM_BASE_URL={provider.base_url}" if provider.base_url else "# CERTO_LLM_API_KEY="
    )
    return [f"# {provider.label}", f"# CERTO_LLM_MODEL={provider.model}", second]


def render_env(providers: list[Provider]) -> str:
    """`.env` with every preset commented out, for the user to fill in."""
    lines = [
        "# Certo settings, written by `certo init`. Keep this file private.",
        "# Nothing is set yet: uncomment the two lines for your provider,",
        "# add your API key (not needed for Ollama), then run: certo check",
        "",
    ]
    for provider in providers:
        preset = _preset_lines(provider)
        if preset:
            lines += [*preset, ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def _folder_has_files(folder: str) -> bool:
    return os.path.isdir(folder) and any(os.scandir(folder))


def _write_private(path: str, text: str) -> None:
    """Write `path` readable by the owner only (600), even if it existed."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def _merge_gitignore(path: str, template: str) -> None:
    """Write the template, or append its missing entries to an existing file."""
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(template)
        return
    with open(path, encoding="utf-8") as f:
        existing = f.read()
    have = {line.strip() for line in existing.splitlines()}
    missing = [
        line
        for line in template.splitlines()
        if line.strip() and not line.startswith("#") and line.strip() not in have
    ]
    if missing:
        with open(path, "a", encoding="utf-8") as f:
            f.write(("" if existing.endswith("\n") or not existing else "\n") + "\n".join(missing))
            f.write("\n")


def write_workspace(folder: str, env_text: str) -> list[str]:
    """Create FOLDER's files. Returns notes about files kept as they were.

    The caller has already decided overwriting is allowed. A README.md that
    isn't one `certo init` wrote is kept, since FOLDER may be an existing
    repo; `.gitignore` only gains the entries it lacks.
    """
    notes = []
    os.makedirs(os.path.join(folder, "tasks"), exist_ok=True)
    _write_private(os.path.join(folder, ".env"), env_text)
    _merge_gitignore(
        os.path.join(folder, ".gitignore"),
        _STARTER.joinpath("gitignore").read_text(encoding="utf-8"),
    )
    for task in sorted(_STARTER.joinpath("tasks").iterdir(), key=lambda t: t.name):
        if task.name.endswith(".md"):
            with open(os.path.join(folder, "tasks", task.name), "w", encoding="utf-8") as f:
                f.write(task.read_text(encoding="utf-8"))
    readme = os.path.join(folder, "README.md")
    if os.path.exists(readme):
        with open(readme, encoding="utf-8") as f:
            ours = f.readline().strip() == README_TITLE
        if not ours:
            notes.append("Kept your existing README.md; Certo's notes were not written.")
            return notes
    with open(readme, "w", encoding="utf-8") as f:
        f.write(_STARTER.joinpath("README.md").read_text(encoding="utf-8"))
    return notes


def build_init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certo init",
        description=(
            "Create a ready-to-use Certo workspace: a minimal .env with your model "
            "settings, sample tasks, and a README with the next steps."
        ),
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=DEFAULT_FOLDER,
        help=f"Folder to create (default: ./{DEFAULT_FOLDER}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Write into a folder that isn't empty, replacing an existing .env and sample tasks.",
    )
    return parser


def init_main(argv: list[str], *, out: TextIO | None = None) -> int:
    out = out or sys.stdout
    args = build_init_parser().parse_args(argv)
    folder = args.folder

    if os.path.exists(folder) and not os.path.isdir(folder):
        print(f"Error: {folder} exists and is not a folder.", file=sys.stderr)
        return 1
    if not args.force:
        if os.path.exists(os.path.join(folder, ".env")):
            print(
                f"Error: {folder}/.env already exists. Use --force to replace it.",
                file=sys.stderr,
            )
            return 1
        if _folder_has_files(folder):
            print(
                f"Error: {folder} is not empty. Use --force to write into it anyway.",
                file=sys.stderr,
            )
            return 1

    providers = load_providers()
    notes = write_workspace(folder, render_env(providers))

    shown = folder.rstrip("/") + "/"
    print(f"Created {shown}", file=out)
    print("  .env          your settings (not committed to git)", file=out)
    print("  tasks/        sample tasks to try", file=out)
    print("  README.md     what to do next", file=out)
    for note in notes:
        print(note, file=out)
    print(
        "\n.env has no model set yet. Open it and uncomment the lines for your provider.", file=out
    )
    print("\nNext:", file=out)
    if os.path.abspath(folder) != os.getcwd():
        print(f"  cd {folder}", file=out)
    print("  certo tasks/wordle.md --project wordle", file=out)
    return 0
