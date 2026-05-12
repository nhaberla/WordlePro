import random
from pathlib import Path
from typing import Annotated, Optional

import typer

from wordlepro.cache import get_cache_path
from wordlepro.controller import BenchmarkController, PlayController, SolveController
from wordlepro.game import WordleGame
from wordlepro.solver import NWordleSolver
from wordlepro.view import WordleView
from wordlepro.words import load_word_lists

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
    answers, guesses = load_word_lists(answers_file, guesses_file)
    view = WordleView()
    if not get_cache_path(answers, guesses).exists():
        view.warn_cache_miss()
    solver = NWordleSolver(boards, max_guesses, answers, guesses)
    SolveController(view, solver, boards, max_guesses).run()


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
    BenchmarkController(WordleView(), answers, guesses, boards, max_guesses, json).run()


@app.command()
def play(
    answers_file: AnswersFile = None,
    guesses_file: GuessesFile = None,
    max_guesses: MaxGuesses = 6,
    word: Annotated[Optional[str], typer.Option("--word", help="Secret word (omit for random)")] = None,
) -> None:
    """Play an interactive Wordle game."""
    answers, guesses = load_word_lists(answers_file, guesses_file)
    valid_guesses: set[str] = set(answers) | set(guesses)

    if word is not None:
        secret = word.strip().lower()
        if secret not in valid_guesses:
            WordleView().show_error(f"{secret!r} is not in the word list.")
            raise typer.Exit(1)
    else:
        secret = random.choice(answers)

    game = WordleGame(secret=secret, max_guesses=max_guesses, valid_guesses=valid_guesses)
    PlayController(WordleView(), game, answers, guesses, max_guesses).run()
