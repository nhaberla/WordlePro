import dataclasses
import json as json_mod
import statistics
from typing import TYPE_CHECKING

import typer
from rich.console import Console, ConsoleRenderable, Group, RichCast
from rich.control import Control
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

from wordlepro.game import WordleGame

if TYPE_CHECKING:
    from wordlepro.benchmark import BenchmarkResult

_TILE_STYLES = ["bold white on grey42", "bold white on dark_goldenrod", "bold white on green"]
_EMPTY_STYLE = "dim white on grey23"
_KEY_STYLES = ["bold white on grey27", "bold white on dark_goldenrod", "bold white on green"]
_KEY_UNGUESSED_STYLE = "bold white on grey58"
_KEYBOARD_ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
_KEYBOARD_INDENTS = ["", "  ", "      "]


class WordleView:
    def __init__(self) -> None:
        self.console = Console()

    # --- Shared ---

    def warn_cache_miss(self) -> None:
        self.console.print("[yellow]Cache not found — computing pattern matrix (one-time, ~10s)…[/yellow]")

    def show_error(self, msg: str) -> None:
        self.console.print(f"[red]{msg}[/red]")

    # --- Solve ---

    def show_solve_status(self, remaining_parts: str, entropy: float, guess_num: int, max_guesses: int) -> None:
        self.console.print(
            Panel(
                f"Remaining answers — {remaining_parts}\nEntropy: {entropy:.2f} bits",
                title=f"Guess {guess_num} / {max_guesses}",
            )
        )

    def show_suggested_guess(self, guess: str, bits: float) -> None:
        self.console.print(f"Suggested guess: [bold]{guess.upper()}[/bold]  ({bits:.2f} bits)")

    def prompt_played_guess(self) -> str:
        return str(typer.prompt("Enter your guess")).strip().lower()

    def prompt_results(self, board_labels: str) -> str:
        return str(typer.prompt(f"Enter results ({board_labels})")).strip()

    def show_results_error(self, msg: str) -> None:
        self.console.print(f"[red]{msg}[/red]")

    def show_board_solved(self, board_index: int) -> None:
        self.console.print(f"[green]✓ Board {board_index + 1} solved![/green]")

    def show_solve_result(self, guess_count: int, solved: bool) -> None:
        if solved:
            self.console.print(
                Panel(
                    f"Solved in {guess_count} guess{'es' if guess_count != 1 else ''}!",
                    title="[green]Success[/green]",
                )
            )
        else:
            self.console.print(
                Panel(
                    f"Out of guesses after {guess_count} attempts.",
                    title="[red]Game Over[/red]",
                )
            )

    # --- Benchmark ---

    def make_progress(self, total: int) -> tuple[Progress, TaskID]:
        progress = Progress(
            SpinnerColumn(),
            "[progress.description]{task.description}",
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )
        task_id = progress.add_task("Benchmarking...", total=total)
        return progress, task_id

    def show_benchmark_json(self, result: "BenchmarkResult") -> None:
        self.console.print(json_mod.dumps(dataclasses.asdict(result), indent=2))

    def show_benchmark_table(self, result: "BenchmarkResult", boards: int, max_guesses: int) -> None:
        dist = result.distribution
        median = int(statistics.median(result.guess_counts))
        std = statistics.stdev(result.guess_counts) if len(result.guess_counts) > 1 else 0.0
        ms_per_word = result.elapsed_seconds / result.total_words * 1000

        title = (
            f"Benchmark Results  "
            f"({result.total_words} words, {boards} board{'s' if boards != 1 else ''}, "
            f"max {max_guesses} guesses)"
        )
        table = Table(title=title, show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("Solved", f"{result.solved}/{result.total_words}")
        table.add_row(f"Failed (>{max_guesses} guesses)", str(len(result.failed_words)))
        table.add_row("Mean guesses", f"{result.mean_guesses:.2f}")
        table.add_row("Median guesses", str(median))
        table.add_row("Std dev", f"{std:.2f}")

        for n in range(1, max_guesses + 1):
            table.add_row(f"{n}-guess wins", str(dist.get(n, 0)))
        table.add_row("Failures", str(dist.get(max_guesses + 1, 0)))

        self.console.print(table)

        if result.failed_words:
            self.console.print(f"Failed words: {', '.join(w.upper() for w in result.failed_words)}")

        self.console.print(f"Total time: {result.elapsed_seconds:.1f}s  ({ms_per_word:.1f}ms per word)")

    # --- Play ---

    def _render_keyboard(self, game: WordleGame) -> Text:
        letter_state: dict[str, int] = {}
        for guess, pattern in zip(game.guesses, game.patterns):
            for ch, p in zip(guess, pattern):
                if ch not in letter_state or p > letter_state[ch]:
                    letter_state[ch] = p

        out = Text()
        for i, row in enumerate(_KEYBOARD_ROWS):
            if i > 0:
                out.append("\n")
            out.append(_KEYBOARD_INDENTS[i])
            for j, ch in enumerate(row):
                if j > 0:
                    out.append(" ")
                style = _KEY_STYLES[letter_state[ch]] if ch in letter_state else _KEY_UNGUESSED_STYLE
                out.append(f" {ch.upper()} ", style=style)
        return out

    def render_board(self, game: WordleGame, max_guesses: int, message: str = "", prompt: str = "") -> Group:
        grid = Table.grid(padding=(0, 1))
        for _ in range(5):
            grid.add_column(justify="center", min_width=3)

        for guess, pattern in zip(game.guesses, game.patterns):
            grid.add_row(*[Text(f" {c.upper()} ", style=_TILE_STYLES[p]) for c, p in zip(guess, pattern)])

        for _ in range(max_guesses - len(game.guesses)):
            grid.add_row(*[Text("   ", style=_EMPTY_STYLE)] * 5)

        keyboard = self._render_keyboard(game)
        layout = Table.grid(padding=(0, 2))
        layout.add_column(vertical="middle")
        layout.add_column(vertical="middle")
        layout.add_row(grid, keyboard)

        status = Text.from_markup(message) if message else Text(" ")
        panel = Panel(Group(layout, status), title="Wordle", subtitle="[dim]h = hint[/dim]")
        return Group(Control.clear(), Control.home(), panel, Text(prompt))

    def prompt_play_input(self) -> str:
        return input("").strip().lower()

    def show_play_result(self, game: WordleGame, secret: str) -> None:
        if game.won:
            n = len(game.guesses)
            self.console.print(Panel(f"Solved in {n} guess{'es' if n != 1 else ''}!", title="[green]You win![/green]"))
        else:
            self.console.print(Panel(f"The word was [bold]{secret.upper()}[/bold].", title="[red]Game over[/red]"))

    def make_live(self, renderable: ConsoleRenderable | RichCast | str | None) -> Live:
        return Live(renderable, auto_refresh=False, console=self.console)
