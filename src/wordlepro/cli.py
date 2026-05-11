from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from wordlepro.solver import NWordleSolver

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
    solver = NWordleSolver.from_files(
        num_boards=boards,
        max_guesses=max_guesses,
        answers_path=answers_file,
        guesses_path=guesses_file,
    )

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
    raise NotImplementedError
