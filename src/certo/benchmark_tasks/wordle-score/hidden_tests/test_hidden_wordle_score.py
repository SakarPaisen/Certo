import pytest
from wordle_score import score_guess

C, P, A = "correct", "present", "absent"


def test_all_correct():
    assert score_guess("crane", "crane") == [C, C, C, C, C]


def test_all_absent():
    assert score_guess("fight", "crane") == [A, A, A, A, A]


def test_case_is_ignored():
    assert score_guess("CrAnE", "crane") == [C, C, C, C, C]


def test_example_from_the_task():
    assert score_guess("robot", "floor") == [P, P, A, C, A]


def test_repeated_guess_letter_with_one_copy_in_answer():
    assert score_guess("speed", "abide") == [A, A, P, A, P]


def test_correct_letters_are_marked_before_present_ones():
    # The two L's in the middle are correct, so the first L has no copy left.
    assert score_guess("lolly", "hello") == [A, P, C, C, A]


def test_repeated_letters_both_present():
    assert score_guess("level", "hello") == [P, C, A, A, P]


def test_extra_copy_after_a_correct_one_is_absent():
    assert score_guess("eerie", "there") == [P, A, P, A, C]


@pytest.mark.parametrize(
    "guess, answer",
    [("four", "crane"), ("crane", "cran3"), ("crane", "cranes"), ("cr ne", "crane")],
)
def test_invalid_words_are_rejected(guess, answer):
    with pytest.raises(ValueError):
        score_guess(guess, answer)
