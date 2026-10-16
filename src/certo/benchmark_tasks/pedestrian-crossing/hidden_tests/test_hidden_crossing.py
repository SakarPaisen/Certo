from crossing import Crossing


def ticks(crossing, n):
    for _ in range(n):
        crossing.tick()


def test_starts_green_without_walk():
    c = Crossing()
    assert c.state == "green"
    assert c.walk is False


def test_stays_green_without_a_press():
    c = Crossing()
    ticks(c, 200)
    assert c.state == "green"


def test_full_cycle_after_a_press_at_the_start():
    c = Crossing()
    c.press_button()
    ticks(c, 9)
    assert c.state == "green"
    c.tick()
    assert c.state == "yellow"
    ticks(c, 2)
    assert c.state == "yellow"
    c.tick()
    assert c.state == "red"
    assert c.walk is True
    ticks(c, 6)
    assert c.state == "red"
    c.tick()
    assert c.state == "green"
    assert c.walk is False


def test_press_after_minimum_green_changes_on_next_tick():
    c = Crossing()
    ticks(c, 25)
    c.press_button()
    assert c.state == "green"
    c.tick()
    assert c.state == "yellow"


def test_press_during_yellow_does_not_cause_another_cycle():
    c = Crossing()
    c.press_button()
    ticks(c, 10)
    assert c.state == "yellow"
    c.press_button()
    ticks(c, 3 + 7)
    assert c.state == "green"
    ticks(c, 10)
    assert c.state == "green"
    ticks(c, 100)
    assert c.state == "green"


def test_press_during_red_is_ignored():
    c = Crossing()
    c.press_button()
    ticks(c, 13)
    assert c.state == "red"
    c.press_button()
    ticks(c, 7)
    assert c.state == "green"
    ticks(c, 10)
    assert c.state == "green"
    ticks(c, 100)
    assert c.state == "green"


def test_minimum_green_applies_again_after_a_cycle():
    c = Crossing()
    c.press_button()
    ticks(c, 20)
    assert c.state == "green"
    c.press_button()
    ticks(c, 9)
    assert c.state == "green"
    c.tick()
    assert c.state == "yellow"


def test_several_presses_count_as_one():
    c = Crossing()
    for _ in range(5):
        c.press_button()
    ticks(c, 10 + 3 + 7)
    assert c.state == "green"
    ticks(c, 10)
    assert c.state == "green"
