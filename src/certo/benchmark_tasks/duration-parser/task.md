# Durations

Write a Python module, using only the standard library.

## `durations.py`

### `parse_duration(text)`

Turns a duration written like `"1h30m"` into a number of seconds (`int`).

- The text has one or more parts. Each part is a whole number directly
  followed by a unit: `h` (hours), `m` (minutes) or `s` (seconds). Units may
  be upper or lower case.
- Parts appear in the order `h`, `m`, `s`, each at most once. Any part may
  be left out.
- Parts may be separated by whitespace (`"2h 5m 10s"`). Leading and
  trailing whitespace is ignored. There is never a space between a number
  and its unit.
- Examples: `"1h30m"` → 5400, `"90s"` → 90, `" 2H 5M "` → 7500, `"0s"` → 0.
- Anything else raises `ValueError`, for example: `""`, `"10"` (no unit),
  `"m"`, `"1h1h"`, `"30m1h"` (wrong order), `"1.5h"`, `"-5m"`, `"5 m"`,
  `"1d"`.

### `format_duration(seconds)`

The opposite direction: a non-negative `int` of seconds to a string.

- Parts are written in the order hours, minutes, seconds, with lower-case
  units, separated by one space: `3661` → `"1h 1m 1s"`.
- Parts that are zero are left out: `3600` → `"1h"`, `3605` → `"1h 5s"`.
- `0` → `"0s"`.
- A negative number raises `ValueError`.

Also write pytest tests for it in `test_durations.py`.
