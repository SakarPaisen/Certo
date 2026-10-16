# Wordle scoring

Write a Python module, using only the standard library.

## `wordle_score.py`

A function `score_guess(guess, answer)` that scores one guess in a
Wordle-style word game and returns a list of five strings, one per letter
of the guess:

- `"correct"`: the right letter in the right place;
- `"present"`: the letter is in the answer, but in another place;
- `"absent"`: the letter is not in the answer (or see below).

Rules:

- Both words must be exactly five letters (`a` to `z`, any case).
  Otherwise raise `ValueError`.
- Comparison ignores case.
- **Repeated letters.** A letter of the answer can only be matched once.
  First mark every `"correct"` letter. Then go through the remaining
  guess letters from left to right: a letter is `"present"` only if the
  answer still has an unmatched copy of it; otherwise it is `"absent"`.

  Example: guess `ROBOT`, answer `FLOOR`. The second `O` of the guess is
  in the right place, so it is `"correct"`. The first `O` then matches the
  answer's other `O`, so it is `"present"`. `R` is `"present"`. `B` and `T`
  are `"absent"`: `["present", "present", "absent", "correct", "absent"]`.

Also write pytest tests for it in `test_wordle_score.py`.
