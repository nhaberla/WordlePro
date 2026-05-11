import dataclasses
import json as json_mod
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table

from wordlepro.benchmark import run_benchmark
from wordlepro.cache import get_cache_path
from wordlepro.solver import NWordleSolver
from wordlepro.words import load_word_lists

app = typer.Typer(pretty_exceptions_show_locals=False)
console = Console()

AnswersFile = Annotated[
    Optional[Path],
    typer.Option("--answers-file", help="Override bundled answers word list"),
]
GuessesFile = Annotated[
    Optional[Path],
    typer.Option("--guesses-file", help="Override bundled guesses word list"),
]
Boards = Annotated[
    int,
    typer.Option("--boards", help="Number of simultaneous boards"),
]
MaxGuesses = Annotated[
    int,
    typer.Option("--max-guesses", help="Maximum guesses allowed"),
]


@app.command()
def solve(
    answers_file: AnswersFile = None,
    guesses_file: GuessesFile = None,
    boards: Boards = 1,
    max_guesses: MaxGuesses = 6,
) -> None:
    """Interactively solve a Wordle game."""
    answers, guesses = load_word_lists(answers_file, guesses_file)
    if not get_cache_path(answers, guesses).exists():
        console.print("[yellow]Cache not found — computing pattern matrix (one-time, ~10s)…[/yellow]")
    solver = NWordleSolver(boards, max_guesses, answers, guesses)

    # Track which boards are solved and how many guesses used
    boards_solved: list[bool] = [False] * boards
    guess_count = 0

    while not solver.game_over:
        # Status panel
        remaining_parts = " ".join(
            f"board {i + 1}: {solver.pattern_matrices[i].shape[1]}"
            for i in range(boards)
            if not boards_solved[i]
        )
        console.print(
            Panel(
                f"Remaining answers — {remaining_parts}\n"
                f"Entropy: {solver.remaining_entropy:.2f} bits",
                title=f"Guess {solver.num_guesses + 1} / {max_guesses}",
            )
        )

        # Suggested guess
        guess, bits = solver.get_guess()
        guess_count += 1
        console.print(f"Suggested guess: [bold]{guess.upper()}[/bold]  ({bits:.2f} bits)")

        # Prompt for the word the user actually played
        played = typer.prompt("Enter your guess").strip().lower()

        # Collect results for each unsolved board
        unsolved_indices = [i for i in range(boards) if not boards_solved[i]]
        board_labels = " ".join(f"b{i + 1}" for i in unsolved_indices)

        while True:
            raw = typer.prompt(f"Enter results ({board_labels})").strip()
            parts = raw.split()
            if len(parts) != len(unsolved_indices):
                console.print(
                    f"[red]Expected {len(unsolved_indices)} result(s), got {len(parts)}. "
                    "Use digits 0 (grey) / 1 (yellow) / 2 (green).[/red]"
                )
                continue

            # Build full results list (solved boards get placeholder "22222")
            full_results: list[str] = []
            part_iter = iter(parts)
            for i in range(boards):
                full_results.append("22222" if boards_solved[i] else next(part_iter))

            try:
                solver.limit_options(played, full_results)
            except (ValueError, KeyError) as exc:
                console.print(f"[red]Invalid input: {exc}[/red]")
                continue
            break

        # Update solved status
        for i in range(boards):
            if not boards_solved[i] and full_results[i] == "22222":
                boards_solved[i] = True
                console.print(f"[green]✓ Board {i + 1} solved![/green]")

    if solver.solved:
        console.print(
            Panel(
                f"Solved in {guess_count} guess{'es' if guess_count != 1 else ''}!",
                title="[green]Success[/green]",
            )
        )
    else:
        console.print(
            Panel(
                f"Out of guesses after {guess_count} attempts.",
                title="[red]Game Over[/red]",
            )
        )


@app.command()
def benchmark(
    answers_file: AnswersFile = None,
    guesses_file: GuessesFile = None,
    boards: Boards = 1,
    max_guesses: MaxGuesses = 6,
    json: Annotated[bool, typer.Option("--json", help="Output results as JSON")] = False,
) -> None:
    """Benchmark the solver against every answer word."""
    answers, guesses = load_word_lists(answers_file, guesses_file)

    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Benchmarking...", total=len(answers))

        def on_progress(n: int) -> None:
            progress.update(task, completed=n)

        result = run_benchmark(answers, guesses, boards, max_guesses, on_progress)

    if json:
        console.print(json_mod.dumps(dataclasses.asdict(result), indent=2))
        return

    dist = result.distribution
    import statistics
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

    console.print(table)

    if result.failed_words:
        console.print(f"Failed words: {', '.join(w.upper() for w in result.failed_words)}")

    console.print(
        f"Total time: {result.elapsed_seconds:.1f}s  ({ms_per_word:.1f}ms per word)"
    )
