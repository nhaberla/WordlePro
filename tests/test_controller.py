import io
import json

import pytest
from rich.console import Console

from wordlepro.cache import get_cache_path
from wordlepro.controller import BenchmarkController, PlayController, SolveController
from wordlepro.game import WordleGame
from wordlepro.solver import NWordleSolver
from wordlepro.view import WordleView

WORDS = [
    "aback", "abase", "abate", "abbey", "abbot",
    "abhor", "abide", "abler", "abode", "abort",
]


class ScriptedView(WordleView):
    """A WordleView that replays canned user input and records output."""

    def __init__(self, inputs: list[str]) -> None:
        super().__init__()
        self.buffer = io.StringIO()
        self.console = Console(file=self.buffer, width=120)
        self._inputs = list(inputs)

    def prompt_play_input(self) -> str:
        return self._inputs.pop(0)


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


class TestSolveControllerRun:
    def test_solves_single_board_after_input_errors(self) -> None:
        # Target is "abase". The script exercises every retry path:
        # an invalid guess, a wrong result count, invalid digits, a
        # contradictory result, then valid play to the solution.
        view = ScriptedView([
            "zz",           # guess error: not 5 letters
            "abbot",        # valid guess
            "0 0",          # wrong number of results (expected 1)
            "00003",        # invalid digit -> ValueError from limit_options
            "00000",        # contradicts clues (every word starts with 'a')
            "22000",        # actual pattern of abbot vs abase
            "abase",        # second guess
            "22222",        # solved
        ])
        solver = NWordleSolver(1, 6, WORDS, WORDS)
        SolveController(view, solver, 1, 6).run()

        assert solver.solved
        assert "Board 1 solved!" in view.buffer.getvalue()
        assert "Solved in 2 guesses!" in view.buffer.getvalue()

    def test_solves_two_boards(self) -> None:
        # Targets: board 1 = "abase", board 2 = "abbot".
        view = ScriptedView([
            "abase",
            "22222 22000",  # board 1 solved; abase vs abbot = 22000
            "abbot",
            "22222",        # only board 2 still prompts
        ])
        solver = NWordleSolver(2, 6, WORDS, WORDS)
        SolveController(view, solver, 2, 6).run()

        assert solver.solved
        # The final live frame shows the last board solved; board 1's
        # solve message was displayed in an earlier (unprinted) frame.
        assert "Board 2 solved!" in view.buffer.getvalue()
        assert "Solved in 2 guesses!" in view.buffer.getvalue()

    def test_out_of_guesses(self) -> None:
        view = ScriptedView([
            "abbot",
            "22000",  # consistent with target "abase" but not solved
        ])
        solver = NWordleSolver(1, 1, WORDS, WORDS)
        SolveController(view, solver, 1, 1).run()

        assert not solver.solved
        assert "Out of guesses after 1 attempts." in view.buffer.getvalue()


class TestPlayControllerRun:
    def make_game(self, secret: str, max_guesses: int = 6) -> WordleGame:
        return WordleGame(secret=secret, max_guesses=max_guesses, valid_guesses=set(WORDS))

    def test_win_with_hint_and_invalid_guess(self) -> None:
        view = ScriptedView([
            "abbot",   # wrong guess, recorded on the board
            "h",       # hint (uses the recorded guess to narrow options)
            "zzzzz",   # invalid word -> error message
            "abase",   # correct
        ])
        # Cold cache exercises the "computing hint cache" notice.
        get_cache_path(WORDS, WORDS).unlink(missing_ok=True)
        game = self.make_game("abase")
        PlayController(view, game, WORDS, WORDS, 6).run()

        assert game.won
        assert "You win!" in view.buffer.getvalue()

    def test_loss_shows_secret(self) -> None:
        view = ScriptedView(["abbot"])
        game = self.make_game("abase", max_guesses=1)
        PlayController(view, game, WORDS, WORDS, 1).run()

        assert game.lost
        out = view.buffer.getvalue()
        assert "Game over" in out
        assert "ABASE" in out


class TestBenchmarkControllerRun:
    def test_table_output_with_failures(self) -> None:
        # With max_guesses=1 the fixed first guess can match at most one
        # target, so failures are guaranteed.
        view = ScriptedView([])
        BenchmarkController(view, WORDS[:4], WORDS, 1, 1, as_json=False).run()
        out = view.buffer.getvalue()
        assert "Benchmark Results" in out
        assert "Failed words:" in out

    def test_json_output(self) -> None:
        view = ScriptedView([])
        BenchmarkController(view, WORDS[:4], WORDS, 1, 6, as_json=True).run()
        # The progress bar's final frame precedes the JSON in the buffer.
        raw = view.buffer.getvalue()
        data = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
        assert data["total_words"] == 4
        assert data["solved"] + len(data["failed_words"]) == 4
