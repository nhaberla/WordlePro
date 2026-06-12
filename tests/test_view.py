import io
import json

import pytest
from rich.console import Console, Group
from rich.live import Live
from rich.progress import Progress

from wordlepro.benchmark import BenchmarkResult
from wordlepro.game import WordleGame
from wordlepro.view import WordleView, _KEY_STYLES, _KEY_UNGUESSED_STYLE


def make_view() -> tuple[WordleView, io.StringIO]:
    view = WordleView()
    buffer = io.StringIO()
    view.console = Console(file=buffer, width=120)
    return view, buffer


def render_to_text(renderable: Group) -> str:
    buffer = io.StringIO()
    Console(file=buffer, width=120).print(renderable)
    return buffer.getvalue()


def make_result(failed: bool = False) -> BenchmarkResult:
    if failed:
        return BenchmarkResult(
            total_words=3,
            solved=2,
            failed_words=["abbot"],
            guess_counts=[2, 3, 7],
            elapsed_seconds=1.5,
        )
    return BenchmarkResult(
        total_words=1,
        solved=1,
        failed_words=[],
        guess_counts=[3],
        elapsed_seconds=0.5,
    )


class TestSharedMessages:
    def test_warn_cache_miss(self) -> None:
        view, buffer = make_view()
        view.warn_cache_miss()
        assert "Cache not found" in buffer.getvalue()

    def test_show_error(self) -> None:
        view, buffer = make_view()
        view.show_error("something broke")
        assert "something broke" in buffer.getvalue()


class TestRenderSolve:
    def test_single_board(self) -> None:
        view, _ = make_view()
        rows = [[("crane", [0, 1, 2, 0, 1])]]
        text = render_to_text(
            view.render_solve(rows, 6, "status here", "message here", "prompt: ")
        )
        assert "Wordle Solver" in text
        assert "C" in text and "E" in text
        assert "status here" in text
        assert "message here" in text
        assert "prompt:" in text

    def test_single_board_empty_status_and_message(self) -> None:
        view, _ = make_view()
        text = render_to_text(view.render_solve([[]], 6, "", "", ""))
        assert "Wordle Solver" in text

    def test_multi_board_shows_labels(self) -> None:
        view, _ = make_view()
        rows = [[("crane", [2] * 5)], [("slate", [0] * 5)]]
        text = render_to_text(view.render_solve(rows, 6, "s", "m", "p"))
        assert "Board 1" in text
        assert "Board 2" in text


class TestShowSolveResult:
    def test_solved_plural(self) -> None:
        view, buffer = make_view()
        view.show_solve_result(3, solved=True)
        assert "Solved in 3 guesses!" in buffer.getvalue()

    def test_solved_singular(self) -> None:
        view, buffer = make_view()
        view.show_solve_result(1, solved=True)
        assert "Solved in 1 guess!" in buffer.getvalue()

    def test_unsolved(self) -> None:
        view, buffer = make_view()
        view.show_solve_result(6, solved=False)
        assert "Out of guesses after 6 attempts." in buffer.getvalue()


class TestBenchmarkOutput:
    def test_make_progress(self) -> None:
        view, _ = make_view()
        progress, task_id = view.make_progress(10)
        assert isinstance(progress, Progress)
        task = next(t for t in progress.tasks if t.id == task_id)
        assert task.total == 10

    def test_show_benchmark_json(self) -> None:
        view, buffer = make_view()
        view.show_benchmark_json(make_result(failed=True))
        data = json.loads(buffer.getvalue())
        assert data["total_words"] == 3
        assert data["failed_words"] == ["abbot"]

    def test_show_benchmark_table_with_failures(self) -> None:
        view, buffer = make_view()
        view.show_benchmark_table(make_result(failed=True), boards=2, max_guesses=6)
        out = buffer.getvalue()
        assert "Benchmark Results" in out
        assert "2 boards" in out
        assert "Solved" in out and "2/3" in out
        assert "Failed words: ABBOT" in out
        assert "Total time:" in out

    def test_show_benchmark_table_single_word_no_failures(self) -> None:
        view, buffer = make_view()
        view.show_benchmark_table(make_result(), boards=1, max_guesses=6)
        out = buffer.getvalue()
        assert "1 board" in out and "1 boards" not in out
        assert "Failed words" not in out
        # stdev with a single sample falls back to 0.00
        assert "0.00" in out


class TestPlayRendering:
    def test_render_board(self) -> None:
        view, _ = make_view()
        game = WordleGame(secret="crane", max_guesses=6, valid_guesses={"crane", "slate"})
        game.submit("slate")
        text = render_to_text(view.render_board(game, 6, message="hello", prompt="> "))
        assert "Wordle" in text
        assert "h = hint" in text
        assert "hello" in text

    def test_render_board_no_message(self) -> None:
        view, _ = make_view()
        game = WordleGame(secret="crane", max_guesses=6, valid_guesses={"crane"})
        text = render_to_text(view.render_board(game, 6))
        assert "Wordle" in text

    def test_keyboard_tracks_best_letter_state(self) -> None:
        view, _ = make_view()
        # 'a' is yellow in the first row, green in the second: green must win.
        rows = [("aback", [1, 0, 0, 0, 0]), ("abase", [2, 0, 0, 0, 0])]
        keyboard = view._render_keyboard(rows)
        a_styles = [
            str(span.style)
            for span in keyboard.spans
            if keyboard.plain[span.start : span.end] == " A "
        ]
        assert a_styles == [_KEY_STYLES[2]]
        q_styles = [
            str(span.style)
            for span in keyboard.spans
            if keyboard.plain[span.start : span.end] == " Q "
        ]
        assert q_styles == [_KEY_UNGUESSED_STYLE]

    def test_prompt_play_input_strips_and_lowers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        view, _ = make_view()
        monkeypatch.setattr("builtins.input", lambda _="": "  CRANE  ")
        assert view.prompt_play_input() == "crane"

    def test_show_play_result_won(self) -> None:
        view, buffer = make_view()
        game = WordleGame(secret="crane", max_guesses=6, valid_guesses={"crane"})
        game.submit("crane")
        view.show_play_result(game, "crane")
        assert "You win!" in buffer.getvalue()
        assert "Solved in 1 guess!" in buffer.getvalue()

    def test_show_play_result_lost(self) -> None:
        view, buffer = make_view()
        game = WordleGame(secret="crane", max_guesses=1, valid_guesses={"crane", "slate"})
        game.submit("slate")
        view.show_play_result(game, "crane")
        assert "Game over" in buffer.getvalue()
        assert "CRANE" in buffer.getvalue()

    def test_make_live(self) -> None:
        view, _ = make_view()
        live = view.make_live("hello")
        assert isinstance(live, Live)
        assert live.console is view.console
