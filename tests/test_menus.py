"""The arrow-key menus' state and the Prompter's choice between menus and
numbered questions. Nothing is drawn: no terminal is needed."""

from __future__ import annotations

import pytest

from certo import menus
from certo.init_cmd import Cancelled, Prompter
from certo.menus import ChecklistState, Row


def _rows():
    return [
        Row("header", "On gpu-box"),
        Row("item", "qwen", "already set up", checked=True),
        Row("item", "gemma"),
        Row("header", "More"),
        Row("action", "DeepSeek models (asks for a key)"),
        Row("action", "Done"),
    ]


def test_the_cursor_skips_headers_and_stops_at_the_ends():
    state = ChecklistState(_rows())
    assert state.position == 1  # the first item, not the header

    state.move(-1)
    assert state.position == 1
    state.move(2)
    assert state.position == 4  # past the "More" header
    state.move(9)
    assert state.position == 5


def test_space_toggles_only_items_and_enter_says_what_to_do():
    state = ChecklistState(_rows())
    state.move(1)
    state.toggle()
    assert state.rows[2].checked is True
    assert state.enter() is None  # Enter on a model: the list is done

    state.move(1)
    state.toggle()  # an action has no check box
    assert state.rows[4].checked is False
    assert state.enter() == 4


def test_the_drawing_marks_the_cursor_and_the_choices():
    text = "".join(fragment for _style, fragment in ChecklistState(_rows()).lines())

    assert "▸ [x] qwen  already set up" in text
    assert "  [ ] gemma" in text
    assert "  DeepSeek models (asks for a key)" in text
    assert menus.HELP in text


def test_prompter_uses_menus_only_when_told_or_on_a_real_terminal(monkeypatch):
    monkeypatch.setattr(menus, "choose", lambda question, options, default=0: 1)

    assert Prompter(menus=True).choose("Pick", ["a", "b"]) == 1
    # Injected input (tests, scripts): numbered questions.
    assert Prompter(input_fn=lambda _p: "2").menus is False


def test_ctrl_c_in_a_menu_cancels(monkeypatch):
    def interrupted(*_a, **_k):
        raise KeyboardInterrupt

    monkeypatch.setattr(menus, "choose", interrupted)
    with pytest.raises(Cancelled):
        Prompter(menus=True).confirm("Sure?")


def test_no_menus_without_a_usable_terminal(monkeypatch):
    monkeypatch.setenv("TERM", "dumb")
    assert menus.available() is False
