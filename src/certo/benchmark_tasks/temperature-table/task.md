# Temperature table

Write a Python module, using only the standard library.

## `temperature.py`

A function `celsius_to_fahrenheit_table(start, stop, step)` that returns a
list of `(celsius, fahrenheit)` tuples.

- `start`, `stop` and `step` are integers.
- The Celsius values go from `start` towards `stop` in steps of `step`.
  **`stop` is included** when a step lands on it exactly. When it doesn't,
  the last value is the last one that doesn't go past `stop`. For example,
  `start=0, stop=10, step=4` gives the Celsius values 0, 4 and 8.
- `step` may be negative, to count down when `start` is greater than
  `stop`.
- When `start == stop`, the table has exactly one row.
- Fahrenheit is `celsius * 9 / 5 + 32`, rounded with `round(value, 1)`.
- Raise `ValueError` when `step` is 0, or when `step` moves away from
  `stop` (for example `start=0, stop=10, step=-1`).

Also write pytest tests for it in `test_temperature.py`.
