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


class TestGetTopGuesses:
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
