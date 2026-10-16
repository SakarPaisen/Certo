# Pedestrian crossing

Write a Python module, using only the standard library, that simulates the
traffic light at a pedestrian crossing.

## `crossing.py`

A class `Crossing` with:

- a property `state`: `"green"`, `"yellow"` or `"red"` (the car light);
- a property `walk`: `True` only while the state is `"red"`;
- a method `press_button()`: a pedestrian asks to cross;
- a method `tick()`: one second passes.

Rules:

- A new `Crossing` is `"green"`.
- Each state counts the seconds since it started: every `tick()` adds one,
  and the count restarts at 0 when the state changes.
- **Green → yellow** happens on the tick where both are true: a press is
  waiting, and green has lasted at least 10 seconds. Without a press, the
  light stays green forever.
- **Yellow → red** happens on the 3rd tick of yellow.
- **Red → green** happens on the 7th tick of red.
- A press while the light is green, or yellow, is remembered as waiting.
  The waiting press is used up when the light turns red. A press while the
  light is red is ignored. So a press during yellow or red never causes an
  extra cycle.

Example: press the button on a new crossing. After 9 ticks it is still
green; the 10th tick makes it yellow; 3 more ticks make it red (walk);
7 more make it green again.

Also write pytest tests for it in `test_crossing.py`.
