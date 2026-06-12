import math
from pathlib import Path

import numpy as np
import pytest

from wordlepro.solver import NWordleSolver

WORDS = [
    "aback", "abase", "abate", "abbey", "abbot",
    "abhor", "abide", "abler", "abode", "abort",
]


def make_solver(num_boards: int = 1, max_guesses: int = 6) -> NWordleSolver:
    return NWordleSolver(num_boards, max_guesses, WORDS, WORDS)


class TestLimitOptions:
    def test_reduces_num_answers(self) -> None:
        solver = make_solver()
        before = solver.num_answers
        guess, _ = solver.get_guess()
        # Use the actual pattern against the first answer so limit_options is valid
        target_col = WORDS.index(WORDS[0])
        base = solver.pattern_matrices[0].copy()
        row = solver.guesses[guess]
        pat = int(base[row, target_col])
        digits = []
        v = pat
        for _ in range(5):
            digits.append(str(v % 3))
            v //= 3
        solver.limit_options(guess, ["".join(digits)])
        assert solver.num_answers < before


class TestLimitOptionsValidation:
    def test_unknown_guess_raises(self) -> None:
        solver = make_solver()
        with pytest.raises(ValueError, match="word list"):
            solver.limit_options("zzzzz", ["00000"])

    def test_wrong_result_count_raises(self) -> None:
        solver = make_solver()
        with pytest.raises(ValueError, match="Expected 1 result"):
            solver.limit_options("aback", ["00000", "00000"])

    def test_wrong_result_length_raises(self) -> None:
        solver = make_solver()
        with pytest.raises(ValueError, match="5 digits"):
            solver.limit_options("aback", ["012"])

    def test_invalid_digits_raise(self) -> None:
        solver = make_solver()
        with pytest.raises(ValueError, match="0, 1, 2"):
            solver.limit_options("aback", ["00003"])

    def test_contradictory_result_raises_and_leaves_state_untouched(self) -> None:
        solver = make_solver()
        before = solver.num_answers
        # Every word starts with 'a', so an all-grey result for "aback"
        # matches no remaining answer.
        with pytest.raises(ValueError, match="contradicts"):
            solver.limit_options("aback", ["00000"])
        assert solver.num_answers == before
        assert solver.boards_solved == [False]


class TestPossibleAnswers:
    def test_shape(self) -> None:
        solver = make_solver()
        solver.get_guess()
        pa = solver.possible_answers()
        assert pa.shape == (len(solver.guesses),)

    def test_non_negative(self) -> None:
        solver = make_solver()
        solver.get_guess()
        assert (solver.possible_answers() >= 0).all()


class TestConvergence:
    @pytest.mark.parametrize("target", WORDS)
    def test_solves_within_max_guesses(self, target: str) -> None:
        solver = make_solver(max_guesses=6)
        target_col = WORDS.index(target)
        base = solver.pattern_matrices[0].copy()

        while not solver.game_over:
            guess, _ = solver.get_guess()
            row = solver.guesses[guess]
            pat = int(base[row, target_col])
            digits = []
            v = pat
            for _ in range(5):
                digits.append(str(v % 3))
                v //= 3
            solver.limit_options(guess, ["".join(digits)])
            if solver.solved:
                break

        assert solver.solved
        assert solver.num_guesses <= 6


class TestFromFiles:
    def test_loads_word_lists_from_paths(self, tmp_path: Path) -> None:
        answers = tmp_path / "answers.txt"
        guesses = tmp_path / "guesses.txt"
        answers.write_text("\n".join(WORDS) + "\n")
        guesses.write_text("\n".join(WORDS) + "\n")
        solver = NWordleSolver.from_files(
            num_boards=1, max_guesses=6, answers_path=answers, guesses_path=guesses
        )
        assert solver.num_answers == len(WORDS)


class TestProperties:
    def test_remaining_entropy_is_log2_of_num_answers(self) -> None:
        solver = make_solver()
        assert solver.remaining_entropy == pytest.approx(math.log2(len(WORDS)))

    def test_reset_restores_initial_state(self) -> None:
        solver = make_solver()
        solver.get_guess()
        solver.limit_options("abbot", ["22000"])
        solver.reset()
        assert solver.num_guesses == 0
        assert solver.num_answers == len(WORDS)
        assert solver.curr_entropies is None


class TestGetTopGuesses:
    def test_before_any_guess_returns_empty(self) -> None:
        solver = make_solver()
        assert solver.get_top_guesses(3) == []

    def test_returns_requested_count(self) -> None:
        solver = make_solver()
        solver.get_guess()
        top = solver.get_top_guesses(3)
        assert len(top) == 3

    def test_returns_word_entropy_tuples(self) -> None:
        solver = make_solver()
        solver.get_guess()
        top = solver.get_top_guesses(3)
        for word, ent in top:
            assert isinstance(word, str)
            assert isinstance(ent, float)

    def test_entropy_descending(self) -> None:
        solver = make_solver()
        solver.get_guess()
        top = solver.get_top_guesses(3)
        entropies = [e for _, e in top]
        assert entropies == sorted(entropies, reverse=True)
