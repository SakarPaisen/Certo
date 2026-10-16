import pytest
from temperature import celsius_to_fahrenheit_table as table


def test_stop_is_included_when_reached():
    assert table(0, 100, 50) == [(0, 32.0), (50, 122.0), (100, 212.0)]


def test_last_value_does_not_pass_stop():
    assert [c for c, _ in table(0, 10, 3)] == [0, 3, 6, 9]


def test_counting_down():
    assert [c for c, _ in table(10, 0, -5)] == [10, 5, 0]


def test_counting_down_without_landing_on_stop():
    assert [c for c, _ in table(10, 1, -4)] == [10, 6, 2]


def test_single_row_when_start_equals_stop():
    assert table(7, 7, 1) == [(7, 44.6)]
    assert table(7, 7, -3) == [(7, 44.6)]


def test_negative_temperatures():
    assert table(-40, -30, 10) == [(-40, -40.0), (-30, -22.0)]


def test_rounding_to_one_decimal():
    assert table(1, 3, 1) == [(1, 33.8), (2, 35.6), (3, 37.4)]


def test_zero_step_is_rejected():
    with pytest.raises(ValueError):
        table(0, 10, 0)


@pytest.mark.parametrize("start, stop, step", [(0, 10, -1), (10, 0, 1)])
def test_step_moving_away_is_rejected(start, stop, step):
    with pytest.raises(ValueError):
        table(start, stop, step)
