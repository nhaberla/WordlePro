from pathlib import Path
from typing import Annotated, Optional

import typer

app = typer.Typer(pretty_exceptions_show_locals=False)

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
    raise NotImplementedError


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
