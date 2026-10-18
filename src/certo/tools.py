"""Assembles the tools available to the agent: the SDK's default preset
(terminal, file editor, task tracker) plus our custom tools.
"""

from __future__ import annotations

from collections.abc import Mapping

from openhands.sdk.tool import Tool
from openhands.tools.preset.default import get_default_tools
from openhands.tools.terminal import TerminalTool

from .custom_tools.run_tests_tool import build_run_tests_tool


def build_tools(terminal_env: Mapping[str, str] | None = None) -> list[Tool]:
    """`terminal_env` is added to the terminal session's environment (e.g.
    the project venv's VIRTUAL_ENV and PATH, see project_env.terminal_env).

    It goes through the tool spec's `params`, which the SDK passes to
    `TerminalTool.create(conv_state, **params)`; `env` there is merged over
    the inherited process environment when the shell starts (via
    `build_terminal_env`). Being part of the serialized spec, it reaches the
    Docker agent-server too.

    The subprocess backend is forced alongside it. Under tmux (the SDK's
    default whenever tmux is installed) the session gets VIRTUAL_ENV but a
    new window takes PATH from the tmux client — Certo's own process — so
    `python` still resolved to Certo's interpreter. Confirmed live with SDK
    1.47.0 and tmux on macOS (see ARCHITECTURE.md's SDK gotchas).
    """
    tools = list(get_default_tools(enable_browser=False))
    if terminal_env:
        params = {"env": dict(terminal_env), "terminal_type": "subprocess"}
        tools = [
            Tool(name=t.name, params={**t.params, **params}) if t.name == TerminalTool.name else t
            for t in tools
        ]
    tools.append(build_run_tests_tool())
    return tools
