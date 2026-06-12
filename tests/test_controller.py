import pytest

from wordlepro.controller import SolveController
from wordlepro.solver import NWordleSolver
from wordlepro.view import WordleView

WORDS = [
    "aback", "abase", "abate", "abbey", "abbot",
    "abhor", "abide", "abler", "abode", "abort",
]


@pytest.fixture(scope="module")
def controller() -> SolveController:
    solver = NWordleSolver(1, 6, WORDS, WORDS)
    return SolveController(WordleView(), solver, 1, 6)


class TestGuessError:
    def test_valid_word(self, controller: SolveController) -> None:
        assert controller._guess_error("aback") is None

    def test_guess_and_result_on_one_line(self, controller: SolveController) -> None:
        error = controller._guess_error("aback 01210")
        assert error is not None and "on one line" in error

    def test_guess_and_result_without_space(self, controller: SolveController) -> None:
        error = controller._guess_error("aback01210")
        assert error is not None and "on one line" in error

    def test_result_entered_first(self, controller: SolveController) -> None:
        error = controller._guess_error("01210")
        assert error is not None and "result" in error

    def test_wrong_length(self, controller: SolveController) -> None:
        error = controller._guess_error("abc")
        assert error is not None and "5-letter" in error

    def test_empty_input(self, controller: SolveController) -> None:
        error = controller._guess_error("")
        assert error is not None and "5-letter" in error

    def test_word_not_in_list(self, controller: SolveController) -> None:
        error = controller._guess_error("zzzzz")
        assert error is not None and "word list" in error
