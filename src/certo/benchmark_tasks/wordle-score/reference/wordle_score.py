from collections import Counter


def _check(word):
    if len(word) != 5 or not word.isascii() or not word.isalpha():
        raise ValueError(f"not a five-letter word: {word!r}")
    return word.lower()


def score_guess(guess, answer):
    guess, answer = _check(guess), _check(answer)
    marks = ["absent"] * 5
    unmatched = Counter()
    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            marks[i] = "correct"
        else:
            unmatched[a] += 1
    for i, g in enumerate(guess):
        if marks[i] != "correct" and unmatched[g] > 0:
            marks[i] = "present"
            unmatched[g] -= 1
    return marks
