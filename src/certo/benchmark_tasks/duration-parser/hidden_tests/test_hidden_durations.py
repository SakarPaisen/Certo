import pytest
from durations import format_duration, parse_duration


@pytest.mark.parametrize(
    "text, seconds",
    [
        ("1h30m", 5400),
        ("90s", 90),
        ("45m", 2700),
        ("2h 5m 10s", 7510),
        (" 2H 5M ", 7500),
        ("0s", 0),
        ("1h  30m", 5400),
        ("100m", 6000),
        ("1h10s", 3610),
    ],
)
def test_valid_durations(text, seconds):
    assert parse_duration(text) == seconds


@pytest.mark.parametrize(
    "text", ["", "   ", "10", "m", "1h1h", "30m1h", "1.5h", "-5m", "5 m", "1d", "1h30", "h1"]
)
def test_invalid_durations(text):
    with pytest.raises(ValueError):
        parse_duration(text)


@pytest.mark.parametrize(
    "seconds, text",
    [
        (3661, "1h 1m 1s"),
        (3600, "1h"),
        (3605, "1h 5s"),
        (59, "59s"),
        (0, "0s"),
        (7200 + 120, "2h 2m"),
    ],
)
def test_format(seconds, text):
    assert format_duration(seconds) == text


def test_format_rejects_negative():
    with pytest.raises(ValueError):
        format_duration(-1)


@pytest.mark.parametrize("seconds", [1, 61, 3599, 3600, 86399])
def test_round_trip(seconds):
    assert parse_duration(format_duration(seconds)) == seconds
