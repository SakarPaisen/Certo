"""Arrow-key menus for `certo init` and `certo init models`, on a real
terminal: one choice (`choose`, `confirm`) with prompt_toolkit's own
`choice()`, and a checklist (`checklist`) built from its application,
key-binding and layout pieces, since prompt_toolkit's only multi-select
is a full-screen dialog. `init_cmd.Prompter` uses them when stdin and
stdout are a terminal (and TERM isn't "dumb"); otherwise, and in every
test, the numbered questions are asked instead.

The checklist's state is `ChecklistState`, plain Python, so its keys are
tested without a terminal; only `checklist()` draws it.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

HELP = "↑↓ move · Space select · Enter done, or open a line under More"


def available() -> bool:
    """Whether menus can be drawn: an interactive terminal on both ends."""
    if os.environ.get("TERM", "") in ("", "dumb"):
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def choose(question: str, options: list[str], default: int = 0) -> int:
    """One of `options`, by index. Ctrl-C raises KeyboardInterrupt."""
    from prompt_toolkit.shortcuts import choice

    return choice(
        message=question,
        options=[(i, option) for i, option in enumerate(options)],
        default=default,
        symbol="▸",
    )


def confirm(question: str, default: bool = True) -> bool:
    return choose(question, ["Yes", "No"], 0 if default else 1) == 0


@dataclass
class Row:
    """A line of a checklist: a group `header` (not selectable), an `item`
    (Space turns it on or off), or an `action` (Enter runs it)."""

    kind: str
    label: str
    note: str = ""
    checked: bool = False


@dataclass
class ChecklistState:
    rows: list[Row]
    position: int = field(default=-1)

    def __post_init__(self) -> None:
        if self.position < 0:
            self.position = self._selectable()[0]

    def _selectable(self) -> list[int]:
        return [i for i, row in enumerate(self.rows) if row.kind != "header"]

    def move(self, step: int) -> None:
        selectable = self._selectable()
        index = selectable.index(self.position) + step
        self.position = selectable[max(0, min(index, len(selectable) - 1))]

    def toggle(self) -> None:
        row = self.rows[self.position]
        if row.kind == "item":
            row.checked = not row.checked

    def enter(self) -> int | None:
        """The row index of the action to run, or None: the list is done."""
        return self.position if self.rows[self.position].kind == "action" else None

    def lines(self) -> list[tuple[str, str]]:
        """(style, text) fragments to draw."""
        out: list[tuple[str, str]] = []
        for i, row in enumerate(self.rows):
            pointer = "▸ " if i == self.position else "  "
            if row.kind == "header":
                out.append(("bold", f"  {row.label}\n"))
                continue
            mark = ("[x] " if row.checked else "[ ] ") if row.kind == "item" else ""
            style = "reverse" if i == self.position else ""
            out.append((style, f"{pointer}{mark}{row.label}"))
            if row.note:
                out.append(("fg:ansibrightblack", f"  {row.note}"))
            out.append(("", "\n"))
        out.append(("fg:ansibrightblack", f"\n{HELP}\n"))
        return out


def checklist(question: str, state: ChecklistState) -> int | None:
    """Draw `state` until Enter. Returns the action row to run, or None
    when the list is done; `state.rows[i].checked` holds the choice.
    Ctrl-C raises KeyboardInterrupt."""
    from prompt_toolkit.application import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import HSplit, Layout, Window
    from prompt_toolkit.layout.controls import FormattedTextControl

    keys = KeyBindings()

    @keys.add("up")
    def _up(event) -> None:
        state.move(-1)

    @keys.add("down")
    def _down(event) -> None:
        state.move(1)

    @keys.add(" ")
    def _space(event) -> None:
        state.toggle()

    @keys.add("enter")
    def _enter(event) -> None:
        event.app.exit(result=state.enter())

    @keys.add("c-c")
    def _cancel(event) -> None:
        event.app.exit(exception=KeyboardInterrupt())

    body = HSplit(
        [
            Window(FormattedTextControl([("bold", question + "\n")]), dont_extend_height=True),
            Window(
                FormattedTextControl(lambda: state.lines()),
                always_hide_cursor=True,
                dont_extend_height=True,
            ),
        ]
    )
    app = Application(layout=Layout(body), key_bindings=keys, full_screen=False)
    return app.run()
