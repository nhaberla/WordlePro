from wordlepro.benchmark import BenchmarkResult, run_benchmark
from wordlepro.cache import get_cache_path
from wordlepro.game import WordleGame
from wordlepro.solver import NWordleSolver
from wordlepro.view import WordleView


class SolveController:
    def __init__(self, view: WordleView, solver: NWordleSolver, boards: int, max_guesses: int) -> None:
        self.view = view
        self.solver = solver
        self.boards = boards
        self.max_guesses = max_guesses

    def run(self) -> None:
        boards_solved: list[bool] = [False] * self.boards
        guess_count = 0

        while not self.solver.game_over:
            remaining_parts = " ".join(
                f"board {i + 1}: {self.solver.pattern_matrices[i].shape[1]}"
                for i in range(self.boards)
                if not boards_solved[i]
            )
            self.view.show_solve_status(
                remaining_parts,
                self.solver.remaining_entropy,
                self.solver.num_guesses + 1,
                self.max_guesses,
            )

            guess, bits = self.solver.get_guess()
            guess_count += 1
            self.view.show_suggested_guess(guess, bits)

            played = self.view.prompt_played_guess()

            unsolved_indices = [i for i in range(self.boards) if not boards_solved[i]]
            board_labels = " ".join(f"b{i + 1}" for i in unsolved_indices)
            full_results: list[str] = []

            while True:
                raw = self.view.prompt_results(board_labels)
                parts = raw.split()
                if len(parts) != len(unsolved_indices):
                    self.view.show_results_error(
                        f"Expected {len(unsolved_indices)} result(s), got {len(parts)}. "
                        "Use digits 0 (grey) / 1 (yellow) / 2 (green)."
                    )
                    continue

                full_results = []
                part_iter = iter(parts)
                for i in range(self.boards):
                    full_results.append("22222" if boards_solved[i] else next(part_iter))

                try:
                    self.solver.limit_options(played, full_results)
                except (ValueError, KeyError) as exc:
                    self.view.show_error(f"Invalid input: {exc}")
                    continue
                break

            for i in range(self.boards):
                if not boards_solved[i] and full_results[i] == "22222":
                    boards_solved[i] = True
                    self.view.show_board_solved(i)

        self.view.show_solve_result(guess_count, self.solver.solved)


class BenchmarkController:
    def __init__(
        self,
        view: WordleView,
        answers: list[str],
        guesses: list[str],
        boards: int,
        max_guesses: int,
        as_json: bool,
    ) -> None:
        self.view = view
        self.answers = answers
        self.guesses = guesses
        self.boards = boards
        self.max_guesses = max_guesses
        self.as_json = as_json

    def run(self) -> None:
        progress, task_id = self.view.make_progress(len(self.answers))

        with progress:
            def on_progress(n: int) -> None:
                progress.update(task_id, completed=n)

            result: BenchmarkResult = run_benchmark(
                self.answers, self.guesses, self.boards, self.max_guesses, on_progress
            )

        if self.as_json:
            self.view.show_benchmark_json(result)
        else:
            self.view.show_benchmark_table(result, self.boards, self.max_guesses)


class PlayController:
    def __init__(
        self,
        view: WordleView,
        game: WordleGame,
        answers: list[str],
        guesses: list[str],
        max_guesses: int,
    ) -> None:
        self.view = view
        self.game = game
        self.answers = answers
        self.guesses = guesses
        self.max_guesses = max_guesses

    def run(self) -> None:
        valid_guesses_list = list(self.game.valid_guesses)
        message = ""

        with self.view.make_live(self.view.render_board(self.game, self.max_guesses)) as live:
            while not self.game.over:
                prompt = f"Guess {len(self.game.guesses) + 1}/{self.max_guesses}: "
                live.update(self.view.render_board(self.game, self.max_guesses, message, prompt))
                live.refresh()
                raw = self.view.prompt_play_input()

                if raw == "h":
                    if not get_cache_path(self.answers, valid_guesses_list).exists():
                        message = "[yellow]Computing hint cache (one-time, ~10s)…[/yellow]"
                        live.update(self.view.render_board(self.game, self.max_guesses, message, prompt))
                        live.refresh()
                    hint_solver = NWordleSolver(1, self.max_guesses, self.answers, self.guesses)
                    for g, pat in zip(self.game.guesses, self.game.patterns):
                        hint_solver.limit_options(g, ["".join(str(v) for v in pat)])
                    hint_word, hint_bits = hint_solver.get_guess()
                    message = f"Hint: [bold]{hint_word.upper()}[/bold] ({hint_bits:.2f} bits)"
                    continue

                try:
                    self.game.submit(raw)
                    message = ""
                except ValueError as exc:
                    message = f"[red]{exc}[/red]"
                    continue

            live.update(self.view.render_board(self.game, self.max_guesses))
            live.refresh()

        self.view.show_play_result(self.game, self.game.secret)
