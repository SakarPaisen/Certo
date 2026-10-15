"""`certo init [FOLDER]`: a ready-to-use workspace in one command.

Writes a minimal `.env`, a `.gitignore`, the sample tasks and a short
README into FOLDER. The provider presets and default models live in
`starter/providers.toml`, the only place they are kept.

On a terminal it asks only what `.env` needs: provider, model, and the API
key (hidden) or the Ollama address. Flags skip their question. With no
terminal and no flags, nothing is asked and every preset is written
commented out. There is no `--api-key` flag: a key on the command line ends
up in shell history, so a key comes from the hidden prompt or from the
provider's own environment variable, never from argv. The key is never
printed or logged.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import tomllib
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from importlib import resources
from typing import TextIO

from .config import ConfigError, load_config
from .llm_check import check_tool_calling, explain

DEFAULT_FOLDER = "certo-workspace"
README_TITLE = "# Certo workspace"

_STARTER = resources.files("certo").joinpath("starter")
_OLLAMA_TIMEOUT_SECONDS = 5
# Generous: a local model may have to load into memory on the first call.
CHECK_TIMEOUT_SECONDS = 120


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


@dataclass(frozen=True)
class Settings:
    """What `.env` will select. `api_key` is never shown in a repr."""

    provider: Provider
    model: str
    api_key: str | None = field(default=None, repr=False)
    # Set instead of api_key: `.env` then refers to this variable, so the
    # key is read from the environment and never copied into the file.
    key_env: str | None = None
    base_url: str | None = None

    @property
    def has_key(self) -> bool:
        return bool(self.api_key or self.key_env)


def _quote(value: str) -> str:
    """Single-quoted for python-dotenv: literal, no `${...}` expansion."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _preset_lines(provider: Provider) -> list[str]:
    """The two commented-out lines that select `provider`."""
    if provider.model is None:
        return []
    second = (
        f"# CERTO_LLM_BASE_URL={provider.base_url}" if provider.base_url else "# CERTO_LLM_API_KEY="
    )
    return [f"# {provider.label}", f"# CERTO_LLM_MODEL={provider.model}", second]


def _active_lines(settings: Settings) -> list[str]:
    lines = [f"# Your model: {settings.provider.label}", f"CERTO_LLM_MODEL={settings.model}"]
    if settings.key_env:
        lines += [
            f"# Read from {settings.key_env} in your environment each time Certo starts.",
            f"CERTO_LLM_API_KEY=${{{settings.key_env}}}",
        ]
    elif settings.api_key:
        lines.append(f"CERTO_LLM_API_KEY={_quote(settings.api_key)}")
    elif settings.provider.key_env or (settings.provider.id == "other" and not settings.base_url):
        where = f" (get one at {settings.provider.key_url})" if settings.provider.key_url else ""
        lines += [f"# Paste your API key after the ={where}.", "CERTO_LLM_API_KEY="]
    if settings.base_url:
        lines.append(f"CERTO_LLM_BASE_URL={settings.base_url}")
    return lines


def render_env(providers: list[Provider], settings: Settings | None = None) -> str:
    """The `.env` text: the chosen settings, then the other providers'
    presets commented out. With no settings, every preset is commented out
    for the user to fill in."""
    lines = ["# Certo settings, written by `certo init`. Keep this file private."]
    if settings is None:
        lines += [
            "# Nothing is set yet: uncomment the two lines for your provider,",
            "# add your API key (not needed for Ollama), then run: certo check",
            "",
        ]
        others = providers
    else:
        lines += [
            "",
            *_active_lines(settings),
            "",
            "# To switch provider, comment out the lines above and uncomment",
            "# the two lines of the provider you want.",
            "",
        ]
        others = [p for p in providers if p.id != settings.provider.id]
    for provider in others:
        preset = _preset_lines(provider)
        if preset:
            lines += [*preset, ""]
    return "\n".join(lines).rstrip("\n") + "\n"


# --- Questions ------------------------------------------------------------------


class Cancelled(Exception):
    """The user stopped answering (Ctrl-C / Ctrl-D)."""


class Prompter:
    """Terminal questions. Injected functions keep it testable."""

    def __init__(
        self,
        *,
        input_fn: Callable[[str], str] = input,
        secret_fn: Callable[[str], str] = getpass.getpass,
        out: TextIO | None = None,
    ) -> None:
        self._input = input_fn
        self._secret = secret_fn
        self.out = out or sys.stdout

    def say(self, text: str = "") -> None:
        print(text, file=self.out, flush=True)

    def _read(self, fn: Callable[[str], str], prompt: str) -> str:
        try:
            return fn(prompt).strip()
        except (EOFError, KeyboardInterrupt) as exc:
            raise Cancelled from exc

    def ask(self, question: str, default: str | None = None) -> str:
        suffix = f" [{default}]" if default else ""
        answer = self._read(self._input, f"{question}{suffix}: ")
        return answer or (default or "")

    def confirm(self, question: str) -> bool:
        while True:
            answer = self._read(self._input, f"{question} [Y/n]: ").lower()
            if answer in ("", "y", "yes"):
                return True
            if answer in ("n", "no"):
                return False
            self.say("Please answer y or n.")

    def choose(self, question: str, options: list[str], default: int = 0) -> int:
        self.say(question)
        for i, option in enumerate(options, start=1):
            self.say(f"  {i}. {option}")
        while True:
            answer = self.ask("Choice", str(default + 1))
            if answer.isdigit() and 1 <= int(answer) <= len(options):
                return int(answer) - 1
            self.say(f"Please enter a number from 1 to {len(options)}.")

    def secret(self, question: str) -> str:
        return self._read(self._secret, f"{question}: ")


def normalize_base_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if url and "://" not in url:
        url = "http://" + url
    return url


def fetch_ollama_models(base_url: str, timeout: float = _OLLAMA_TIMEOUT_SECONDS) -> list[str]:
    """Names of the models installed on an Ollama server (`/api/tags`).
    Raises OSError (URLError included) when the server can't be reached."""
    with urllib.request.urlopen(f"{base_url}/api/tags", timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return [m["name"] for m in data.get("models", []) if m.get("name")]


def _provider_for_model(providers: list[Provider], model: str) -> Provider:
    prefix = model.split("/", 1)[0] if "/" in model else ""
    if prefix == "ollama_chat":
        prefix = "ollama"
    by_id = {p.id: p for p in providers}
    return by_id.get(prefix) or by_id["other"]


def _with_prefix(provider: Provider, model: str) -> str:
    """`claude-sonnet-5-5` typed for Anthropic means `anthropic/claude-sonnet-5-5`."""
    if provider.id == "other" or "/" in model:
        return model
    return f"{provider.id}/{model}"


def _ollama_name(model: str | None) -> str:
    return (model or "").split("/", 1)[-1]


def _ask_ollama(
    provider: Provider,
    args: argparse.Namespace,
    prompter: Prompter,
    ask: bool,
    fetch_models: Callable[[str], list[str]],
) -> Settings:
    default_url = provider.base_url or "http://localhost:11434"
    base_url = args.base_url or (
        prompter.ask("Ollama address", default_url) if ask else default_url
    )
    base_url = normalize_base_url(base_url)
    if args.model:
        return Settings(provider, _with_prefix(provider, args.model), base_url=base_url)

    try:
        installed = fetch_models(base_url)
    except (OSError, ValueError):
        prompter.say(
            f"Couldn't reach Ollama at {base_url}. Check that Ollama is running and "
            "that the address is right. If it runs on another machine, start it "
            "there with OLLAMA_HOST=0.0.0.0 so it accepts connections from this one."
        )
        installed = None
    if installed == []:
        prompter.say("This Ollama server has no models yet. Pull one, then run: certo check")
        prompter.say(f"  ollama pull {_ollama_name(provider.model)}")
        if provider.small_model:
            prompter.say(
                f"  ollama pull {_ollama_name(provider.small_model)}"
                "   (smaller, for machines with less memory)"
            )
    if not installed:
        model = prompter.ask("Model", provider.model) if ask else provider.model
        return Settings(provider, _with_prefix(provider, model or ""), base_url=base_url)

    coder = next((i for i, name in enumerate(installed) if "coder" in name.lower()), 0)
    index = prompter.choose("Which installed model?", installed, coder) if ask else coder
    return Settings(provider, f"ollama/{installed[index]}", base_url=base_url)


def gather_settings(
    args: argparse.Namespace,
    prompter: Prompter,
    *,
    providers: list[Provider],
    env: Mapping[str, str],
    interactive: bool,
    fetch_models: Callable[[str], list[str]] = fetch_ollama_models,
) -> Settings | None:
    """Ask what `.env` needs. None means "write every preset commented out"."""
    if not interactive and not (args.yes or args.provider or args.model):
        return None
    ask = interactive and not args.yes
    if ask:
        prompter.say("Certo setup. Press Enter to accept the default in [brackets].\n")

    by_id = {p.id: p for p in providers}
    if args.provider:
        provider = by_id[args.provider]
    elif args.model:
        provider = _provider_for_model(providers, args.model)
    else:
        found = next((p for p in providers if p.key_env and env.get(p.key_env)), None)
        default = providers.index(found) if found else 0
        index = (
            prompter.choose(
                "Which model provider do you want to use?", [p.label for p in providers], default
            )
            if ask
            else default
        )
        provider = providers[index]
        prompter.say()

    if provider.id == "ollama":
        return _ask_ollama(provider, args, prompter, ask, fetch_models)

    if provider.id == "other":
        model = args.model or ""
        while not model:
            if not ask:
                raise ValueError("--provider other needs --model (any LiteLLM model id).")
            model = prompter.ask("LiteLLM model id (for example deepseek/deepseek-chat)")
        api_key = prompter.secret("API key (hidden, Enter to skip)") if ask else ""
        base_url = args.base_url or (prompter.ask("Base URL (Enter to skip)") if ask else "")
        return Settings(
            provider,
            model,
            api_key=api_key or None,
            base_url=normalize_base_url(base_url) if base_url else None,
        )

    model = args.model or (prompter.ask("Model", provider.model) if ask else provider.model)
    model = _with_prefix(provider, model or "")
    base_url = normalize_base_url(args.base_url) if args.base_url else None
    found = provider.key_env and env.get(provider.key_env)
    if found and (
        not ask or prompter.confirm(f"Found {provider.key_env} in your environment. Use it?")
    ):
        return Settings(provider, model, key_env=provider.key_env, base_url=base_url)
    api_key = prompter.secret("API key (hidden)") if ask else ""
    return Settings(provider, model, api_key=api_key or None, base_url=base_url)


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


def _provider_name(model: str) -> str | None:
    """'Anthropic' for an anthropic/ model: the provider label without the
    parenthesized note, for the plain-language check messages."""
    provider = _provider_for_model(load_providers(), model)
    if provider.id == "other":
        return None
    return provider.label.split(" (", 1)[0]


def run_check(
    env: Mapping[str, str] | None, out: TextIO, *, timeout: int = CHECK_TIMEOUT_SECONDS
) -> bool:
    """The test call behind `certo init` and `certo check`: one tool call
    through the configured model, reported as one plain line. `env` None
    reads the settings as a run does (environment, then ./.env)."""
    try:
        cfg = load_config(env)
    except ConfigError as exc:
        print(f"Checking the model... not configured: {exc}", file=out)
        return False
    local = cfg.model.split("/", 1)[0] in ("ollama", "ollama_chat")
    wait = " (a local model may take a minute to load)" if local else ""
    print(f"Checking the model {cfg.model}{wait}...", end=" ", file=out, flush=True)
    result = check_tool_calling(cfg, timeout=timeout)
    print(explain(result, _provider_name(cfg.model)), file=out)
    return result.ok


def _settings_env(settings: Settings, env: Mapping[str, str]) -> dict[str, str]:
    """The CERTO_LLM_* values the written .env resolves to."""
    values = {"CERTO_LLM_MODEL": settings.model}
    key = settings.api_key or (env.get(settings.key_env, "") if settings.key_env else "")
    if key:
        values["CERTO_LLM_API_KEY"] = key
    if settings.base_url:
        values["CERTO_LLM_BASE_URL"] = settings.base_url
    return values


def build_check_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certo check",
        description=(
            "Check that the configured model works: one small real call, which "
            "must come back as a tool call, since that's what Certo's agent "
            "needs. Reads the settings exactly as a run does: exported "
            "CERTO_LLM_* variables, then .env in the current folder."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=CHECK_TIMEOUT_SECONDS,
        help=f"Seconds to wait for the answer (default {CHECK_TIMEOUT_SECONDS}).",
    )
    return parser


def check_main(argv: list[str], *, out: TextIO | None = None) -> int:
    """`certo check`: re-run init's model check against the current settings."""
    args = build_check_parser().parse_args(argv)
    out = out or sys.stdout
    if not os.path.exists(".env") and not os.environ.get("CERTO_LLM_MODEL"):
        print(
            "No settings here: this folder has no .env and CERTO_LLM_MODEL isn't set. "
            "Run certo check in the folder certo init created, or run certo init.",
            file=out,
        )
        return 1
    ok = run_check(None, out, timeout=args.timeout)
    if not ok:
        print("Fix .env as described, then run: certo check", file=out)
    return 0 if ok else 1


def build_init_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="certo init",
        description=(
            "Create a ready-to-use Certo workspace: a minimal .env with your model "
            "settings, sample tasks, and a README with the next steps. On a "
            "terminal it asks a few questions; each flag below skips one."
        ),
        epilog=(
            "There is no --api-key flag, on purpose: a key typed on the command "
            "line is saved in your shell history. Type it at the hidden prompt, "
            "or export the provider's own variable (OPENAI_API_KEY, "
            "ANTHROPIC_API_KEY or GEMINI_API_KEY) first and init offers to use it. "
            "Without a terminal and without flags, nothing is asked and .env is "
            "written with every provider commented out for you to fill in."
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
    parser.add_argument(
        "--provider",
        choices=[p.id for p in load_providers()],
        default=None,
        help="Model provider; skips that question.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id, e.g. anthropic/claude-sonnet-5-5; skips that question.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Server address, for Ollama or a self-hosted model; skips that question.",
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="Don't make the test call to the model after writing .env.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Ask nothing and accept every default. A key is used only from the environment.",
    )
    return parser


def init_main(
    argv: list[str],
    *,
    prompter: Prompter | None = None,
    env: Mapping[str, str] | None = None,
    interactive: bool | None = None,
    fetch_models: Callable[[str], list[str]] = fetch_ollama_models,
) -> int:
    prompter = prompter or Prompter()
    out = prompter.out
    env = os.environ if env is None else env
    interactive = sys.stdin.isatty() if interactive is None else interactive
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
    try:
        settings = gather_settings(
            args,
            prompter,
            providers=providers,
            env=env,
            interactive=interactive,
            fetch_models=fetch_models,
        )
    except Cancelled:
        print("\nCancelled. Nothing was written.", file=out)
        return 130
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    notes = write_workspace(folder, render_env(providers, settings))

    checkable = settings is not None and (settings.has_key or settings.base_url)
    checked_ok = None
    if checkable and not args.no_check:
        checked_ok = run_check(_settings_env(settings, env), out)
        if not checked_ok:
            print(
                f"Your settings are saved in {os.path.join(folder, '.env')}. Fix them "
                "as described, then run certo check in that folder.",
                file=out,
            )
        print(file=out)

    if settings is not None and interactive and not args.yes:
        print(file=out)
    shown = folder.rstrip("/") + "/"
    print(f"Created {shown}", file=out)
    print("  .env          your settings (not committed to git)", file=out)
    print("  tasks/        sample tasks to try", file=out)
    print("  README.md     what to do next", file=out)
    for note in notes:
        print(note, file=out)
    if settings is None:
        print(
            "\nNo terminal, so nothing was asked: .env has no model set yet. Open it "
            "and uncomment the lines for your provider.",
            file=out,
        )
    elif not settings.has_key and settings.provider.id != "ollama" and not settings.base_url:
        print(
            "\nNo API key yet. Open .env and paste it after CERTO_LLM_API_KEY=.",
            file=out,
        )
    print("\nNext:", file=out)
    if os.path.abspath(folder) != os.getcwd():
        print(f"  cd {folder}", file=out)
    if checked_ok is not True:
        print("  certo check", file=out)
    print("  certo tasks/wordle.md --project wordle", file=out)
    return 0
